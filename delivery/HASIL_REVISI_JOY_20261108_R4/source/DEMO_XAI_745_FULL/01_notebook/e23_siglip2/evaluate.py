"""Joint nested selection of frozen SigLIP2-only and semantic/visual fusion models."""
import os
for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[key] = '1'
import fcntl
import hashlib
import json
from pathlib import Path
import sys
import time
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin, clone
from sklearn.metrics import f1_score, confusion_matrix, classification_report
from sklearn.model_selection import GridSearchCV, ParameterGrid, StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, normalize
from sklearn.svm import SVC
sys.path.append(str(Path(__file__).resolve().parents[1]))
from e16_hierarchical import inputs, outer, sha, save

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / '04_hasil_eksperimen/e23_oof'
EMB = ROOT / '04_hasil_eksperimen/e23_siglip2'
OPTIONS = dict(clf__C=[1, 10, 100], clf__gamma=['scale', .1, 1], clf__class_weight=[None, 'balanced'])
GRID = [dict(fusion__mode=['image_only'], **OPTIONS),
        dict(fusion__mode=['fusion'], fusion__visual_weight=[0, .5, 1, 2, 4],
             fusion__e5_weight=[.5, 2], fusion__clip_weight=[0, 1], **OPTIONS)]
digest = lambda x: hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest()


class VisualFusion(TransformerMixin, BaseEstimator):
    def __init__(self, mode='image_only', visual_weight=1, e5_weight=1, clip_weight=1):
        self.mode = mode; self.visual_weight = visual_weight
        self.e5_weight = e5_weight; self.clip_weight = clip_weight

    def fit(self, x, y=None):
        assert x.shape[1] == 3840 and self.mode in ('image_only', 'fusion')
        self.blocks_ = [((3072, 3840), 1)] if self.mode == 'image_only' else [
            ((0, 1536), self.e5_weight), ((1536, 2560), 1), ((2560, 3072), self.clip_weight),
            ((3072, 3840), self.visual_weight)]
        self.scalers_ = [StandardScaler().fit(x[:, a:b]) for (a, b), _ in self.blocks_]
        return self

    def transform(self, x):
        result = np.hstack([normalize(scaler.transform(x[:, a:b])) * weight
                            for scaler, ((a, b), weight) in zip(self.scalers_, self.blocks_)])
        assert np.isfinite(result).all()
        return result

    def metadata(self):
        return [dict(start=a, stop=b, weight=weight, mean_sha256=digest(scaler.mean_),
                     scale_sha256=digest(scaler.scale_))
                for scaler, ((a, b), weight) in zip(self.scalers_, self.blocks_)]


def pipeline():
    return Pipeline([('fusion', VisualFusion()), ('clf', SVC(kernel='rbf'))])


def load_inputs():
    verified = json.loads((EMB / 'verification.json').read_text())
    assert verified['status'] == 'verified' and verified['samples'] == 740 and verified['dimension'] == 768
    assert verified['verifier_sha256'] == sha(Path(__file__).with_name('verify_features.py'))
    for name, value in verified['sha256'].items():
        assert sha(EMB / name) == value
    meta = json.loads((EMB / 'meta.json').read_text())
    assert meta['signature']['worker_sha256'] == sha(Path(__file__).with_name('extract.py'))
    assert meta['signature']['model_snapshot']['model'] == 'google/siglip2-base-patch16-384'
    assert meta['signature']['model_snapshot']['revision'] == 'f775b65a79762255128c981547af89addcfe0f88'
    df, original, reference = inputs()
    features = np.load(EMB / 'embeddings.npz', allow_pickle=False)
    assert features['sample_id'].tolist() == df.sample_id.to_list() and features['image'].shape == (740, 768)
    x = np.hstack([original, features['image']])
    assert x.shape == (740, 3840) and np.isfinite(x).all()
    signature = dict(worker_sha256=sha(Path(__file__)),
                     helper_sha256=sha(ROOT / '01_notebook/e16_hierarchical.py'), reference=reference,
                     embedding_verification_sha256=sha(EMB / 'verification.json'),
                     embedding_meta_sha256=sha(EMB / 'meta.json'), features_sha256=digest(x), grid=GRID,
                     outer='Task1 baseline5 seed42', inner='Task2 stratified3 seed42',
                     normalization='training-only per-block StandardScaler/L2 then weights', n_jobs=1)
    return df, x, df.task2_domain_sumber.to_numpy(), sorted(set(df.task2_domain_sumber)), list(outer(df)), signature


def selected_inner(x, y, train, options):
    scores, metadata = [], []
    splits = list(StratifiedKFold(3, shuffle=True, random_state=42).split(np.zeros(len(train)), y[train]))
    for a, b in splits:
        model = pipeline().set_params(**options).fit(x[train[a]], y[train[a]])
        pred = model.predict(x[train[b]])
        scores.append(float(f1_score(y[train[b]], pred, average='macro', zero_division=0)))
        metadata.append(model.named_steps['fusion'].metadata())
    return scores, metadata


def main():
    df, x, y, labels, folds, signature = load_inputs()
    OUT.mkdir(exist_ok=True)
    lock = (OUT / 'run.lock').open('a'); fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    protocol = OUT / 'protocol.json'
    if protocol.exists():
        assert json.loads(protocol.read_text()) == signature
    else:
        save(protocol, signature)
    parameters = list(ParameterGrid(GRID)); assert len(parameters) == 378
    predictions = np.empty(740, object); fold_ids = np.zeros(740, int)
    for k, (train, test) in enumerate(folds, 1):
        checkpoint = OUT / f'fold_{k}.json'
        if checkpoint.exists():
            record = json.loads(checkpoint.read_text())
            assert record['signature'] == signature and record['train_indices'] == train.tolist() and record['test_indices'] == test.tolist()
            assert record['sample_ids'] == df.sample_id.iloc[test].to_list()
        else:
            started = time.monotonic()
            search = GridSearchCV(pipeline(), GRID, scoring='f1_macro', n_jobs=1, error_score='raise',
                                  cv=StratifiedKFold(3, shuffle=True, random_state=42))
            search.fit(x[train], y[train]); best = int(search.best_index_)
            assert search.cv_results_['params'] == parameters
            scores = np.column_stack([search.cv_results_[f'split{j}_test_score'] for j in range(3)])
            assert best == int(np.argmax(scores.mean(axis=1)))
            reproduced, fits = selected_inner(x, y, train, parameters[best])
            assert np.allclose(reproduced, scores[best], rtol=0, atol=1e-12)
            pred = search.predict(x[test])
            record = dict(signature=signature, fold=k, train_indices=train.tolist(), test_indices=test.tolist(),
                          sample_ids=df.sample_id.iloc[test].to_list(), predictions=pred.tolist(),
                          grid_params=parameters, inner_fold_scores=scores.tolist(), best_index=best,
                          best_params=parameters[best], inner_macro_f1=float(search.best_score_),
                          selected_inner_fit=fits, outer_fit=search.best_estimator_.named_steps['fusion'].metadata(),
                          seconds=time.monotonic() - started)
            save(checkpoint, record)
            print(json.dumps(dict(fold=k, params=parameters[best], inner_macro_f1=record['inner_macro_f1'],
                                  seconds=record['seconds'])), flush=True)
        predictions[test] = record['predictions']; fold_ids[test] = k
    assert set(predictions) <= set(labels)
    pd.DataFrame(dict(sample_id=df.sample_id, truth=y, prediction=predictions, fold=fold_ids)).to_csv(OUT / 'oof.csv', index=False)
    save(OUT / 'metrics.json', dict(samples=740, macro_f1=float(f1_score(y, predictions, average='macro', zero_division=0)),
         confusion_matrix=confusion_matrix(y, predictions, labels=labels).tolist(),
         classification=classification_report(y, predictions, labels=labels, output_dict=True, zero_division=0),
         signature=signature, oof_sha256=sha(OUT / 'oof.csv')))
    print('OOF COMPLETE; independent audit required', flush=True)


if __name__ == '__main__':
    main()
