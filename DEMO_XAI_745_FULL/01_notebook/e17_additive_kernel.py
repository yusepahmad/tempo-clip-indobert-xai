"""Nested positive sum of modality RBF kernels; E14 verified frozen inputs."""
import os
for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[key] = '1'
import fcntl
import json
from pathlib import Path
import time
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.metrics import classification_report, confusion_matrix, f1_score
from sklearn.metrics.pairwise import rbf_kernel
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.svm import SVC
from e14_weighted_fusion import BlockFusion
from e16_hierarchical import inputs, outer, save, sha

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '04_hasil_eksperimen/e17_additive_kernel'

class AdditiveSVC(ClassifierMixin, BaseEstimator):
    def __init__(self, C=1, gamma=1, class_weight=None, e5_weight=1, clip_weight=1):
        self.C = C
        self.gamma = gamma
        self.class_weight = class_weight
        self.e5_weight = e5_weight
        self.clip_weight = clip_weight

    def kernel(self, a, b):
        assert a.shape[1] == b.shape[1] == 3072
        assert self.e5_weight >= 0 and self.clip_weight >= 0 and self.gamma > 0
        result = np.zeros((len(a), len(b)))
        for (start, end), weight in zip(((0, 1536), (1536, 2560), (2560, 3072)),
                                        (self.e5_weight, 1, self.clip_weight)):
            result += weight * rbf_kernel(a[:, start:end], b[:, start:end], gamma=self.gamma)
        return result / (self.e5_weight + 1 + self.clip_weight)

    def fit(self, x, y):
        self.train_ = np.array(x, copy=True)
        self.model_ = SVC(kernel='precomputed', C=self.C, class_weight=self.class_weight)
        self.model_.fit(self.kernel(x, self.train_), y)
        self.classes_ = self.model_.classes_
        return self

    def predict(self, x):
        return self.model_.predict(self.kernel(x, self.train_))

def pipeline():
    return Pipeline([('fusion', BlockFusion(e5_weight=1, clip_weight=1)), ('clf', AdditiveSVC())])

def main():
    OUT.mkdir(exist_ok=True)
    lock = (OUT / 'run.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    df, x, reference = inputs()
    y = df.task2_domain_sumber.to_numpy()
    labels = sorted(set(y))
    grid = {'clf__C': [1, 10, 100], 'clf__gamma': [.1, 1, 10],
            'clf__class_weight': [None, 'balanced'], 'clf__e5_weight': [.5, 2],
            'clf__clip_weight': [.5, 1, 2]}
    signature = {'worker_sha256': sha(Path(__file__)),
                 'input_helper_sha256': sha(Path(__file__).with_name('e16_hierarchical.py')),
                 'reference': reference, 'grid': grid, 'n_jobs': 1,
                 'outer': 'Task1 baseline stratified5 seed42', 'inner': 'Task2 stratified3 seed42',
                 'kernel': 'positive weighted mean of three per-block RBF kernels',
                 'transform': 'StandardScaler/L2 per block fit only current training, all weights1'}
    save(OUT / 'protocol.json', signature)
    predictions = np.empty(740, object)
    fold_ids = np.zeros(740, int)
    records = []
    for k, (tr, te) in enumerate(outer(df), 1):
        path = OUT / f'fold_{k}.json'
        if path.exists():
            record = json.loads(path.read_text())
            assert record['signature'] == signature and record['train_indices'] == tr.tolist()
            assert record['test_indices'] == te.tolist() and record['sample_ids'] == df.sample_id.iloc[te].tolist()
        else:
            started = time.monotonic()
            search = GridSearchCV(pipeline(), grid, scoring='f1_macro', n_jobs=1, error_score='raise',
                                 cv=StratifiedKFold(3, shuffle=True, random_state=42))
            search.fit(x[tr], y[tr])
            record = {'signature': signature, 'fold': k, 'train_indices': tr.tolist(),
                      'test_indices': te.tolist(), 'sample_ids': df.sample_id.iloc[te].tolist(),
                      'params': search.best_params_, 'inner_macro_f1': float(search.best_score_),
                      'grid_results': [{'params': p, 'mean_inner_macro_f1': float(s)} for p, s in
                                       zip(search.cv_results_['params'], search.cv_results_['mean_test_score'])],
                      'predictions': search.predict(x[te]).tolist(), 'seconds': time.monotonic() - started}
            save(path, record)
            print(json.dumps({key: record[key] for key in ('fold', 'params', 'inner_macro_f1', 'seconds')}), flush=True)
        predictions[te] = record['predictions']
        fold_ids[te] = k
        records.append(record)
    assert all(value in labels for value in predictions)
    pd.DataFrame({'sample_id': df.sample_id, 'truth': y, 'prediction': predictions,
                  'fold': fold_ids}).to_csv(OUT / 'additive_oof.csv', index=False)
    save(OUT / 'additive.json', {'samples': 740,
         'macro_f1': float(f1_score(y, predictions, average='macro', zero_division=0)),
         'classification': classification_report(y, predictions, output_dict=True, zero_division=0),
         'confusion_matrix': confusion_matrix(y, predictions, labels=labels).tolist(),
         'folds': records, 'signature': signature})
    print('COMPLETE E17', f1_score(y, predictions, average='macro', zero_division=0), flush=True)

if __name__ == '__main__':
    main()
