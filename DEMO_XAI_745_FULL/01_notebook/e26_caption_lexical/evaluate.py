"""Nested evaluation of fold-fitted sparse caption phrases and frozen E14 features."""
import os
for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[key] = '1'
import fcntl
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time
import numpy as np
import pandas as pd
import scipy
from scipy import sparse
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import classification_report, confusion_matrix, f1_score
from sklearn.metrics.pairwise import linear_kernel, rbf_kernel
from sklearn.model_selection import ParameterGrid, StratifiedKFold
from sklearn.preprocessing import StandardScaler, normalize
from sklearn.svm import SVC

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / '04_hasil_eksperimen/e26_caption_lexical'
sys.path.append(str(ROOT / '01_notebook'))
spec = importlib.util.spec_from_file_location('e26_e22_reference', ROOT / '01_notebook/e22_caption_low/evaluate.py')
REFERENCE = importlib.util.module_from_spec(spec)
spec.loader.exec_module(REFERENCE)
sha, save, digest = REFERENCE.sha, REFERENCE.save, REFERENCE.digest
COMMON = dict(view=['caption', 'context'], analyzer=['word', 'word_char'], C=[.1, 1, 10, 100],
              kernel=['linear', 'rbf'], class_weight=[None, 'balanced'])
GRID = [dict(semantic_weight=[0], lexical_weight=[1], **COMMON),
        dict(semantic_weight=[1], lexical_weight=[.5, 1, 2], **COMMON)]


def text_inputs(df, captions):
    assert len(df) == len(captions) == 740
    assert [r['sample_id'] for r in captions] == df.sample_id.to_list()
    text = [r['caption'] for r in captions]
    assert all(isinstance(s, str) and len(s) >= 40 for s in text)
    context = [a + '\n' + str(b) + ' ' + str(c) for a, b, c in
               zip(text, df.headline_verified, df.supporting_text_verified)]
    return dict(caption=np.asarray(text, object), context=np.asarray(context, object))


def load_inputs():
    assert sha(Path(spec.origin)) == '2436276fd51f42a0be511c2eb354782d192a39f653bcecf3ed0b3fb70df19244'
    df, x, y, labels, folds, reference = REFERENCE.load_inputs()
    caption_dir = ROOT / '04_hasil_eksperimen/e22_caption_low'
    manifest = json.loads((caption_dir / 'verification.json').read_text())
    assert manifest['status'] == 'verified' and manifest['samples'] == 740
    assert manifest['verifier_sha256'] == sha(ROOT / '01_notebook/e22_caption_low/verify.py')
    for name, value in manifest['sha256'].items():
        assert sha(caption_dir / name) == value
    captions = [json.loads(line) for line in (caption_dir / 'captions.jsonl').read_text().splitlines()]
    texts = text_inputs(df, captions)
    semantic = x[:, :3072]
    signature = dict(worker_sha256=sha(Path(__file__)), reference=reference,
        caption_verification_sha256=sha(caption_dir / 'verification.json'),
        captions_sha256=sha(caption_dir / 'captions.jsonl'), semantic_sha256=digest(semantic),
        texts_sha256={key: hashlib.sha256(json.dumps(value.tolist(), ensure_ascii=False).encode()).hexdigest()
                      for key, value in texts.items()}, grid=GRID,
        versions=dict(numpy=np.__version__, scipy=scipy.__version__, sklearn=sklearn.__version__),
        lexical='training-only word1:2/max12000; optional char_wb3:5/max24000; min_df1/sublinear; union L2; no SVD',
        semantic='training-only per-block StandardScaler/L2; E5=.5 BGE=1 CLIP=1',
        outer='original Task1 baseline5 seed42', inner='Task2 stratified3 seed42; first argmax',
        backend='float64 sparse projection; cached linear/RBF(scale) Gram; precomputed SVC', n_jobs=1)
    return df, semantic, texts, y, labels, folds, signature


class Features:
    def fit(self, semantic, texts, train, view, analyzer):
        self.view = view
        self.analyzer = analyzer
        self.scalers = [StandardScaler().fit(semantic[train, a:b]) for a, b in
                        [(0, 1536), (1536, 2560), (2560, 3072)]]
        self.vectorizers = [TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True,
                                          max_features=12000, dtype=np.float64)]
        assert analyzer in ('word', 'word_char') and view in ('caption', 'context')
        if analyzer == 'word_char':
            self.vectorizers.append(TfidfVectorizer(analyzer='char_wb', ngram_range=(3, 5), min_df=1,
                sublinear_tf=True, max_features=24000, dtype=np.float64))
        for vectorizer in self.vectorizers:
            vectorizer.fit(texts[view][train])
        return self

    def transform(self, semantic, texts, indices):
        base = np.asarray(np.hstack([normalize(s.transform(semantic[indices, a:b])) * w
            for s, (a, b), w in zip(self.scalers, [(0, 1536), (1536, 2560), (2560, 3072)], [.5, 1, 1])]), dtype=np.float64)
        lexical = normalize(sparse.hstack([v.transform(texts[self.view][indices])
                                           for v in self.vectorizers], format='csr'))
        assert np.isfinite(base).all() and np.isfinite(lexical.data).all()
        return sparse.csr_matrix(base), lexical

    def metadata(self):
        return dict(view=self.view, analyzer=self.analyzer,
            scalers=[dict(start=a, stop=b, weight=w, mean_sha256=digest(s.mean_), scale_sha256=digest(s.scale_))
                for s, (a, b), w in zip(self.scalers, [(0, 1536), (1536, 2560), (2560, 3072)], [.5, 1, 1])],
            lexical=[dict(dimension=len(v.vocabulary_), vocabulary_sha256=hashlib.sha256(
                json.dumps({word: int(index) for word, index in v.vocabulary_.items()}, sort_keys=True).encode()).hexdigest(), idf_sha256=digest(v.idf_))
                for v in self.vectorizers])


def prepare(semantic, texts, train, test, view, analyzer):
    assert not set(train) & set(test)
    model = Features().fit(semantic, texts, train, view, analyzer)
    return dict(train=model.transform(semantic, texts, train), test=model.transform(semantic, texts, test),
                metadata=model.metadata(), kernels={})


def projection(pair, options):
    base, lexical = pair
    return sparse.hstack([base * options['semantic_weight'], lexical * options['lexical_weight']], format='csr')


def gamma_scale(train):
    variance = float(train.multiply(train).mean() - train.mean() ** 2)
    return 1 / (train.shape[1] * variance) if variance else 1.0


def kernels(cache, options):
    key = (options['semantic_weight'], options['lexical_weight'], options['kernel'])
    if key not in cache['kernels']:
        a, b = projection(cache['train'], options), projection(cache['test'], options)
        if options['kernel'] == 'linear':
            train, test = linear_kernel(a, a), linear_kernel(b, a)
        else:
            gamma = gamma_scale(a)
            train, test = rbf_kernel(a, a, gamma=gamma), rbf_kernel(b, a, gamma=gamma)
        cache['kernels'][key] = train, test
    return cache['kernels'][key]


def predict(cache, options, y):
    train, test = kernels(cache, options)
    return SVC(kernel='precomputed', C=options['C'], class_weight=options['class_weight']).fit(train, y).predict(test)


def raw_fit_predict(semantic, texts, train, test, options, y):
    model = Features().fit(semantic, texts, train, options['view'], options['analyzer'])
    a = projection(model.transform(semantic, texts, train), options)
    b = projection(model.transform(semantic, texts, test), options)
    classifier = SVC(kernel=options['kernel'], C=options['C'], gamma='scale', class_weight=options['class_weight'])
    classifier.fit(a, y)
    return classifier.predict(b), model.metadata(), classifier._gamma


def main():
    df, semantic, texts, y, labels, folds, signature = load_inputs()
    OUT.mkdir(exist_ok=True)
    lock = (OUT / 'run.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    protocol = OUT / 'protocol.json'
    if protocol.exists():
        assert json.loads(protocol.read_text()) == signature
    else:
        save(protocol, signature)
    parameters = list(ParameterGrid(GRID))
    assert len(parameters) == 256
    predictions = np.empty(740, object)
    fold_ids = np.zeros(740, int)
    for k, (train, test) in enumerate(folds, 1):
        checkpoint = OUT / f'fold_{k}.json'
        if checkpoint.exists():
            r = json.loads(checkpoint.read_text())
            assert r['signature'] == signature and r['train_indices'] == train.tolist() and r['test_indices'] == test.tolist()
            assert r['sample_ids'] == df.sample_id.iloc[test].to_list()
        else:
            started = time.monotonic()
            inner = list(StratifiedKFold(3, shuffle=True, random_state=42).split(np.zeros(len(train)), y[train]))
            caches = {}
            for view in COMMON['view']:
                for analyzer in COMMON['analyzer']:
                    caches[(view, analyzer)] = [prepare(semantic, texts, train[a], train[b], view, analyzer) for a, b in inner]
            scores = [[float(f1_score(y[train[b]], predict(cache, options, y[train[a]]), average='macro', zero_division=0))
                       for (a, b), cache in zip(inner, caches[(options['view'], options['analyzer'])])]
                      for options in parameters]
            means = np.mean(scores, axis=1)
            best = int(np.argmax(means))
            options = parameters[best]
            selected = caches[(options['view'], options['analyzer'])]
            fit = [cache['metadata'] for cache in selected]
            del caches, selected
            outer_cache = prepare(semantic, texts, train, test, options['view'], options['analyzer'])
            pred = predict(outer_cache, options, y[train])
            r = dict(signature=signature, fold=k, train_indices=train.tolist(), test_indices=test.tolist(),
                sample_ids=df.sample_id.iloc[test].to_list(), predictions=pred.tolist(), grid_params=parameters,
                inner_fold_scores=scores, best_index=best, best_params=options, inner_macro_f1=float(means[best]),
                selected_inner_fit=fit, outer_fit=outer_cache['metadata'], seconds=time.monotonic()-started)
            save(checkpoint, r)
            print(json.dumps(dict(fold=k, params=options, inner_macro_f1=float(means[best]), seconds=r['seconds'])), flush=True)
        predictions[test] = r['predictions']
        fold_ids[test] = k
    assert set(predictions) <= set(labels)
    pd.DataFrame(dict(sample_id=df.sample_id, truth=y, prediction=predictions, fold=fold_ids)).to_csv(OUT / 'oof.csv', index=False)
    save(OUT / 'metrics.json', dict(samples=740, macro_f1=float(f1_score(y, predictions, average='macro', zero_division=0)),
        confusion_matrix=confusion_matrix(y, predictions, labels=labels).tolist(),
        classification=classification_report(y, predictions, labels=labels, output_dict=True, zero_division=0),
        signature=signature, oof_sha256=sha(OUT / 'oof.csv')))
    print('E26 OOF COMPLETE; raw sparse SVC audit required', flush=True)


if __name__ == '__main__':
    main()
