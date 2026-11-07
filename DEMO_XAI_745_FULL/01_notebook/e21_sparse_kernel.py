"""Nested numeric RBF plus uncompressed fold-fitted lexical cosine kernel."""
import os
for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[key] = '1'
import fcntl
import hashlib
import json
from pathlib import Path
import time
import numpy as np
import pandas as pd
from scipy.sparse import hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import classification_report, confusion_matrix, f1_score
from sklearn.metrics.pairwise import euclidean_distances
from sklearn.model_selection import ParameterGrid, StratifiedKFold
from sklearn.preprocessing import StandardScaler, normalize
from sklearn.svm import SVC
from e16_hierarchical import inputs, outer, save, sha

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '04_hasil_eksperimen/e21_sparse_kernel'
BLOCKS = ((0, 1536), (1536, 2560), (2560, 3072))
GRID = dict(e5_weight=[.5, 2], clip_weight=[.5, 1], gamma=[.1, 1],
            lexical_weight=[0, .25, 1, 4], C=[1, 10, 100], class_weight=[None, 'balanced'])
TFIDF = dict(min_df=2, sublinear_tf=True)
digest_array = lambda x: hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest()

def gate():
    prior = ROOT / '04_hasil_eksperimen/e20_zero_shot_fusion'
    verified = json.loads((prior / 'verification.json').read_text())
    assert verified['status'] == 'verified' and verified['samples'] == 740
    assert verified['verifier_sha256'] == sha(Path(__file__).with_name('e20_zero_shot_fusion_verify.py'))
    for name, digest in verified['sha256'].items():
        assert sha(prior / name) == digest
    assert verified['macro_f1'] < .70, 'Target candidate requires root completion audit first'
    return sha(prior / 'verification.json')

def load_inputs():
    launch_verification = gate()
    df, x, reference = inputs()
    folder = ROOT / '04_hasil_eksperimen/e01_vlm/kaggle_full/e01_vlm'
    sources = []
    source_hashes = {}
    for name, digest in [('deskripsi.jsonl', 'c75e8df3f9b71d6786462f8d0f1187ebe4234fb8dd079924f3f35707ff1b8cd2'),
                         ('zeroshot.jsonl', '10c07b06b13fbbf647f2b1ed12a722d9bff8f97caa6b621430d8bc0429ab38c9')]:
        path = folder / name
        assert sha(path) == digest
        source_hashes[name] = digest
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        lookup = {row['sample_id']: row for row in rows}
        assert len(rows) == len(lookup) == 740 and set(lookup) == set(df.sample_id)
        sources.append([lookup[sid] for sid in df.sample_id])
    def texts_for(frame):
        return np.array([' '.join([a['deskripsi'], b.get('sumber_visual') or '',
                                  b.get('alasan') or '', title, support])
                         for a, b, title, support in zip(*sources, frame.headline_verified,
                                                        frame.supporting_text_verified)])
    texts = texts_for(df)
    permuted = df.copy()
    permuted['task2_domain_sumber'] = df.task2_domain_sumber.iloc[::-1].to_numpy()
    assert np.array_equal(texts, texts_for(permuted))
    y = df.task2_domain_sumber.to_numpy()
    labels = sorted(set(y))
    assert len(df) == 740 and df.sample_id.is_unique and len(labels) == 7
    folds = list(outer(df))
    assert len(folds) == 5 and all(len(tr) == 592 and len(te) == 148 for tr, te in folds)
    signature = dict(worker_sha256=sha(Path(__file__)), input_helper_sha256=sha(Path(__file__).with_name('e16_hierarchical.py')),
                     e14_source_sha256=sha(Path(__file__).with_name('e14_weighted_fusion.py')),
                     reference=reference, text_sources=source_hashes,
                     texts_sha256=hashlib.sha256(json.dumps(texts.tolist(), ensure_ascii=False).encode()).hexdigest(),
                     feature_sha256=digest_array(x), grid=GRID, tfidf=TFIDF,
                     launch_e20_verification_sha256=launch_verification,
                     text_fields='E01 description/source/reason; original headline/support only',
                     kernel='(RBF weighted block squared distance + lambda*cosine TFIDF)/(1+lambda)',
                     outer='Task1 baseline5 seed42', inner='Task2 stratified3 seed42', n_jobs=1)
    return df, x, texts, y, labels, folds, signature

def prepare(x, texts, train, test):
    """Fit every learned transform solely on the supplied training indices."""
    train = np.asarray(train, dtype=int); test = np.asarray(test, dtype=int)
    assert not set(train) & set(test) and len(set(train)) == len(train)
    distance_train, distance_test, metadata = [], [], []
    for a, b in BLOCKS:
        scaler = StandardScaler().fit(x[train, a:b])
        tr = normalize(scaler.transform(x[train, a:b]))
        te = normalize(scaler.transform(x[test, a:b]))
        distance_train.append(np.maximum(euclidean_distances(tr, tr, squared=True), 0))
        distance_test.append(np.maximum(euclidean_distances(te, tr, squared=True), 0))
        metadata.append(dict(mean_sha256=digest_array(scaler.mean_), scale_sha256=digest_array(scaler.scale_)))
    vectors = [TfidfVectorizer(ngram_range=(1, 2), max_features=12000, **TFIDF),
               TfidfVectorizer(analyzer='char_wb', ngram_range=(3, 5), max_features=24000, **TFIDF)]
    lexical_train, lexical_test, lexical_meta = [], [], []
    for vector in vectors:
        lexical_train.append(vector.fit_transform(texts[train]))
        lexical_test.append(vector.transform(texts[test]))
        vocabulary = {key: int(value) for key, value in vector.vocabulary_.items()}
        lexical_meta.append(dict(vocabulary_sha256=hashlib.sha256(json.dumps(vocabulary, sort_keys=True).encode()).hexdigest(),
                                 idf_sha256=digest_array(vector.idf_), features=len(vector.vocabulary_)))
    tr = normalize(hstack(lexical_train, format='csr'))
    te = normalize(hstack(lexical_test, format='csr'))
    fit = dict(training_indices_sha256=digest_array(train), training_samples=len(train),
               numeric=metadata, lexical=lexical_meta)
    return dict(train_distances=distance_train, test_distances=distance_test,
                train_lexical=(tr @ tr.T).toarray(), test_lexical=(te @ tr.T).toarray(), fit=fit)

def kernel(prepared, params, test=False):
    distances = prepared['test_distances' if test else 'train_distances']
    weighted = sum(weight ** 2 * distance for weight, distance in
                   zip((params['e5_weight'], 1, params['clip_weight']), distances))
    lexical = prepared['test_lexical' if test else 'train_lexical']
    value = (np.exp(-params['gamma'] * weighted) + params['lexical_weight'] * lexical) / (1 + params['lexical_weight'])
    assert np.isfinite(value).all()
    if not test:
        assert np.allclose(value, value.T, atol=1e-12)
    return value

def predict(prepared, params, y_train):
    model = SVC(kernel='precomputed', C=params['C'], class_weight=params['class_weight'])
    model.fit(kernel(prepared, params), y_train)
    return model.predict(kernel(prepared, params, test=True))

def main():
    df, x, texts, y, labels, folds, signature = load_inputs()
    OUT.mkdir(exist_ok=True)
    lock = (OUT / 'run.lock').open('a'); fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    protocol = OUT / 'protocol.json'
    if protocol.exists():
        assert json.loads(protocol.read_text()) == signature
    else:
        save(protocol, signature)
    params = list(ParameterGrid(GRID)); assert len(params) == 192
    prediction = np.empty(740, object); fold_ids = np.zeros(740, int)
    for k, (train, test) in enumerate(folds, 1):
        checkpoint = OUT / f'fold_{k}.json'
        if checkpoint.exists():
            record = json.loads(checkpoint.read_text())
            assert record['signature'] == signature and record['train_indices'] == train.tolist() and record['test_indices'] == test.tolist()
            assert record['sample_ids'] == df.sample_id.iloc[test].to_list()
        else:
            started = time.monotonic()
            inner = list(StratifiedKFold(3, shuffle=True, random_state=42).split(np.zeros(len(train)), y[train]))
            prepared = [prepare(x, texts, train[a], train[b]) for a, b in inner]
            scores = []
            for options in params:
                scores.append([float(f1_score(y[train[b]], predict(cache, options, y[train[a]]),
                                              average='macro', zero_division=0))
                               for (a, b), cache in zip(inner, prepared)])
            means = np.mean(scores, axis=1); best = int(np.argmax(means))
            full = prepare(x, texts, train, test)
            pred = predict(full, params[best], y[train])
            record = dict(signature=signature, fold=k, train_indices=train.tolist(), test_indices=test.tolist(),
                          sample_ids=df.sample_id.iloc[test].to_list(), predictions=pred.tolist(),
                          grid_params=params, inner_fold_scores=scores, best_index=best,
                          inner_macro_f1=float(means[best]), best_params=params[best],
                          inner_fit=[p['fit'] for p in prepared], outer_fit=full['fit'],
                          seconds=time.monotonic() - started)
            save(checkpoint, record)
            print(json.dumps(dict(fold=k, inner_macro_f1=record['inner_macro_f1'], params=params[best],
                                  seconds=record['seconds'])), flush=True)
        prediction[test] = record['predictions']; fold_ids[test] = k
    assert all(value in labels for value in prediction)
    pd.DataFrame(dict(sample_id=df.sample_id, truth=y, prediction=prediction, fold=fold_ids)).to_csv(OUT / 'oof.csv', index=False)
    report = dict(samples=740, macro_f1=float(f1_score(y, prediction, average='macro', zero_division=0)),
                  confusion_matrix=confusion_matrix(y, prediction, labels=labels).tolist(),
                  classification=classification_report(y, prediction, labels=labels, output_dict=True, zero_division=0),
                  signature=signature, oof_sha256=sha(OUT / 'oof.csv'))
    save(OUT / 'metrics.json', report); print('COMPLETE E21', report['macro_f1'], flush=True)

if __name__ == '__main__':
    main()
