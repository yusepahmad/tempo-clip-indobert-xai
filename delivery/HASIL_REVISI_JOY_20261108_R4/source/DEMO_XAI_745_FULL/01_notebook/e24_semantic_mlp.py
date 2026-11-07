"""Nested MLP on frozen semantic/visual E14 inputs; training-only transformations and weights."""
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
sys.path.append(str(Path(__file__).resolve().parent))
from e16_hierarchical import inputs, outer, sha, save

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '04_hasil_eksperimen/e24_semantic_mlp'
from e14_weighted_fusion import BlockFusion
from sklearn.base import ClassifierMixin
from sklearn.neural_network import MLPClassifier
from sklearn.utils.class_weight import compute_sample_weight
from sklearn.exceptions import ConvergenceWarning
import warnings
import sklearn

GRID = dict(fusion__e5_weight=[.5, 2], clf__alpha=[.01, 1],
            clf__balanced=[False, True], clf__max_iter=[50, 150])
digest = lambda x: hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest()


class AuditedFusion(BlockFusion):
    def metadata(self):
        return [dict(start=a, stop=b, weight=w, mean_sha256=digest(s.mean_), scale_sha256=digest(s.scale_))
                for s, (a, b), w in zip(self.scalers_, [(0,1536),(1536,2560),(2560,3072)],
                                       [self.e5_weight,1,self.clip_weight])]


class BalancedMLP(ClassifierMixin, BaseEstimator):
    def __init__(self, alpha=.01, balanced=False, max_iter=50):
        self.alpha=alpha; self.balanced=balanced; self.max_iter=max_iter

    def fit(self, x, y):
        self.classes_=np.unique(y); assert len(self.classes_)==7
        weights=compute_sample_weight('balanced',y) if self.balanced else np.ones(len(y))
        self.training_weight_sha256_=digest(weights)
        self.model_=MLPClassifier(hidden_layer_sizes=(64,), activation='relu', solver='adam',
            alpha=self.alpha, batch_size=len(y), learning_rate_init=.003, max_iter=self.max_iter,
            shuffle=True, random_state=42, tol=0, early_stopping=False, n_iter_no_change=self.max_iter+1)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always',ConvergenceWarning)
            self.model_.fit(x,y,sample_weight=weights)
        self.warnings_=[str(w.message) for w in caught]
        assert self.model_.n_iter_==self.max_iter
        assert all(np.isfinite(a).all() for a in self.model_.coefs_+self.model_.intercepts_)
        assert np.isfinite(self.model_.loss_curve_).all()
        return self

    def predict(self,x):
        prob=self.model_.predict_proba(x)
        assert np.isfinite(prob).all() and np.allclose(prob.sum(axis=1),1)
        return self.classes_[prob.argmax(axis=1)]

    def metadata(self):
        return dict(n_iter=self.model_.n_iter_, loss_curve=list(map(float,self.model_.loss_curve_)),
            classes=self.classes_.tolist(), training_weight_sha256=self.training_weight_sha256_,
            weight_sha256=[digest(a) for a in self.model_.coefs_+self.model_.intercepts_],
            warnings=self.warnings_)


def pipeline():
    return Pipeline([('fusion',AuditedFusion(clip_weight=1)),('clf',BalancedMLP())])


def fit_metadata(model):
    return dict(fusion=model.named_steps['fusion'].metadata(), classifier=model.named_steps['clf'].metadata())


def load_inputs():
    assert sklearn.__version__=='1.7.2'
    df,x,reference=inputs()
    signature=dict(worker_sha256=sha(Path(__file__)), helper_sha256=sha(Path(__file__).with_name('e16_hierarchical.py')),
        fusion_sha256=sha(Path(__file__).with_name('e14_weighted_fusion.py')), reference=reference,
        features_sha256=digest(x), grid=GRID, outer='Task1 baseline5 seed42', inner='Task2 stratified3 seed42',
        normalization='training-only per-block StandardScaler/L2 then weights', sklearn=sklearn.__version__,
        fixed=dict(hidden=64,activation='relu',solver='adam',lr=.003,seed=42,batch='fulltraining',
                   early_stopping=False,tol=0,threads=1))
    return df,x,df.task2_domain_sumber.to_numpy(),sorted(set(df.task2_domain_sumber)),list(outer(df)),signature


def selected_inner(x, y, train, options):
    scores, metadata = [], []
    splits = list(StratifiedKFold(3, shuffle=True, random_state=42).split(np.zeros(len(train)), y[train]))
    for a, b in splits:
        model = pipeline().set_params(**options).fit(x[train[a]], y[train[a]])
        pred = model.predict(x[train[b]])
        scores.append(float(f1_score(y[train[b]], pred, average='macro', zero_division=0)))
        metadata.append(fit_metadata(model))
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
    parameters = list(ParameterGrid(GRID)); assert len(parameters) == 16
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
                          selected_inner_fit=fits, outer_fit=fit_metadata(search.best_estimator_),
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
