"""Nested literal/metaphor gate plus six-domain SVC; frozen E14 inputs."""
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
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.metrics import classification_report, confusion_matrix, f1_score
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.svm import SVC
from e14_weighted_fusion import BlockFusion

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '04_hasil_eksperimen/e16_hierarchical'
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()

class HierarchicalSVC(ClassifierMixin, BaseEstimator):
    def __init__(self, C=1, gamma='scale', class_weight=None, threshold=0):
        self.C = C
        self.gamma = gamma
        self.class_weight = class_weight
        self.threshold = threshold

    def fit(self, x, y):
        y = np.asarray(y)
        self.classes_ = np.unique(y)
        nonmeta = y == 'NON_METAFORA'
        assert len(self.classes_) == 7 and nonmeta.any() and (~nonmeta).any()
        options = dict(C=self.C, gamma=self.gamma, class_weight=self.class_weight, kernel='rbf')
        self.gate_ = SVC(**options).fit(x, nonmeta)
        self.domain_ = SVC(**options).fit(x[~nonmeta], y[~nonmeta])
        assert self.gate_.classes_.tolist() == [False, True] and len(self.domain_.classes_) == 6
        return self

    def predict(self, x):
        result = self.domain_.predict(x).astype(object)
        result[self.gate_.decision_function(x) >= self.threshold] = 'NON_METAFORA'
        return result

def save(path, value):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    temporary.replace(path)

def inputs():
    reference = ROOT / '04_hasil_eksperimen/e14_weighted_fusion'
    audit = json.loads((reference / 'verification.json').read_text())
    assert audit['status'] == 'verified' and audit['samples'] == 740
    assert sha(reference / 'verification.json') == '3bcb7e4e22cb744c41d088e643dfac936796bde2248df14ca22878fa26df40db'
    for name, digest in audit['sha256'].items():
        assert sha(reference / name) == digest
    source = json.loads((reference / 'protocol.json').read_text())
    assert sha(Path(__file__).with_name('e14_weighted_fusion.py')) == source['worker_sha256']
    csv = ROOT / '03_data/DATASET_740_TASK2_DOMAIN.csv'
    assert sha(csv) == source['data_sha256'] == 'cba20f8250bcb59481ed2d3d7d5d42fb8242c96a7ba2d11a2cd02ad80862961a'
    df = pd.read_csv(csv).fillna('')
    paths = [ROOT / '04_hasil_eksperimen/e06_semantic/e06_semantic/embeddings.npz',
             ROOT / '04_hasil_eksperimen/e13_bge_m3/e13_bge_m3/embeddings.npz',
             ROOT / '03_data/fitur_clip_indobert_740.npz']
    for key, path in zip(('e5_sha256', 'bge_sha256', 'clip_sha256'), paths):
        assert sha(path) == source[key]
    e5, bge, clip = [np.load(path, allow_pickle=False) for path in paths]
    assert np.array_equal(e5['sample_id'], df.sample_id) and np.array_equal(bge['sample_id'], df.sample_id)
    x = np.hstack([e5['description'], e5['source_reason'], bge['combined'], clip['img']])
    assert x.shape == (740, 3072) and np.isfinite(x).all()
    return df, x, source

def outer(df):
    issues = pd.Categorical(df.task1_issue, categories=sorted(set(df.task1_issue))).codes
    counts = np.bincount(issues)
    strat = np.array([i if counts[i] >= 5 else -1 for i in issues])
    return list(StratifiedKFold(5, shuffle=True, random_state=42).split(np.zeros(740), strat))

def pipeline():
    return Pipeline([('fusion', BlockFusion(clip_weight=1)), ('clf', HierarchicalSVC())])

def main():
    OUT.mkdir(exist_ok=True)
    lock = (OUT / 'run.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    df, x, source = inputs()
    y = df.task2_domain_sumber.to_numpy()
    labels = sorted(set(y))
    grid = {'fusion__e5_weight': [.5, 2], 'clf__C': [1, 10], 'clf__gamma': ['scale', .1],
            'clf__class_weight': [None, 'balanced'], 'clf__threshold': [-.5, 0, .5]}
    signature = {'worker_sha256': sha(Path(__file__)), 'reference': source, 'grid': grid,
                 'outer': 'Task1 baseline stratified5 seed42', 'inner': 'Task2 stratified3 seed42',
                 'gate': 'decision_function NON_METAFORA >= threshold',
                 'domain_training': 'only non-NON_METAFORA training samples', 'n_jobs': 1}
    save(OUT / 'protocol.json', signature)
    records = []
    predictions = np.empty(740, object)
    fold_ids = np.zeros(740, int)
    for k, (tr, te) in enumerate(outer(df), 1):
        path = OUT / f'fold_{k}.json'
        if path.exists():
            record = json.loads(path.read_text())
            assert record['signature'] == signature and record['train_indices'] == tr.tolist()
            assert record['test_indices'] == te.tolist() and record['sample_ids'] == df.sample_id.iloc[te].tolist()
        else:
            started = time.monotonic()
            search = GridSearchCV(pipeline(), grid, scoring='f1_macro',
                                 cv=StratifiedKFold(3, shuffle=True, random_state=42),
                                 n_jobs=1, error_score='raise')
            search.fit(x[tr], y[tr])
            pred = search.predict(x[te])
            record = {'signature': signature, 'fold': k, 'train_indices': tr.tolist(),
                      'test_indices': te.tolist(), 'sample_ids': df.sample_id.iloc[te].tolist(),
                      'params': search.best_params_, 'inner_macro_f1': float(search.best_score_),
                      'grid_results': [{'params': p, 'mean_inner_macro_f1': float(s)} for p, s in
                                       zip(search.cv_results_['params'], search.cv_results_['mean_test_score'])],
                      'predictions': pred.tolist(), 'seconds': time.monotonic() - started}
            save(path, record)
            print(json.dumps({key: record[key] for key in ('fold', 'params', 'inner_macro_f1', 'seconds')}), flush=True)
        predictions[te] = record['predictions']
        fold_ids[te] = k
        records.append(record)
    assert all(pred in labels for pred in predictions)
    pd.DataFrame({'sample_id': df.sample_id, 'truth': y, 'prediction': predictions,
                  'fold': fold_ids}).to_csv(OUT / 'hierarchical_oof.csv', index=False)
    report = {'samples': 740, 'macro_f1': float(f1_score(y, predictions, average='macro', zero_division=0)),
              'classification': classification_report(y, predictions, output_dict=True, zero_division=0),
              'confusion_matrix': confusion_matrix(y, predictions, labels=labels).tolist(),
              'folds': records, 'signature': signature}
    save(OUT / 'hierarchical.json', report)
    print('COMPLETE E16', report['macro_f1'], flush=True)

if __name__ == '__main__':
    main()
