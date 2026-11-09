"""Nested PCA/gradient boosting on audited frozen semantic and caption features."""
import os
for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[key] = '1'
import fcntl
import hashlib
import importlib.util
import json
from pathlib import Path
import time
import numpy as np
import pandas as pd
import sklearn
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.decomposition import PCA
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import f1_score, confusion_matrix, classification_report
from sklearn.model_selection import GridSearchCV, ParameterGrid, StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, normalize
from sklearn.utils.class_weight import compute_sample_weight
from e16_hierarchical import inputs, outer, sha, save

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '04_hasil_eksperimen/e29_pca_boosting'
GRID = dict(fusion__mode=['semantic', 'caption_fusion'], fusion__n_components=[32, 64],
            clf__max_leaf_nodes=[7, 15], clf__l2_regularization=[1, 10],
            clf__max_iter=[100, 300], clf__class_weight=[None, 'balanced'])
digest = lambda x: hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest()


class BlockPCA(TransformerMixin, BaseEstimator):
    def __init__(self, mode='semantic', n_components=32):
        self.mode = mode; self.n_components = n_components

    def fit(self, x, y=None):
        assert x.shape[1] == 4096 and self.mode in ('semantic', 'caption_fusion')
        self.blocks_ = [(0, 1536), (1536, 2560), (2560, 3072)]
        if self.mode == 'caption_fusion':
            self.blocks_.append((3072, 4096))
        self.scalers_, self.pcas_ = [], []
        for a, b in self.blocks_:
            scaler = StandardScaler().fit(x[:, a:b])
            pca = PCA(n_components=self.n_components, svd_solver='randomized', random_state=42,
                      iterated_power=4, power_iteration_normalizer='QR', whiten=False)
            pca.fit(normalize(scaler.transform(x[:, a:b])))
            assert np.isfinite(pca.components_).all() and pca.n_samples_ == len(x)
            self.scalers_.append(scaler); self.pcas_.append(pca)
        return self

    def transform(self, x):
        values = np.hstack([pca.transform(normalize(scaler.transform(x[:, a:b])))
                           for (a, b), scaler, pca in zip(self.blocks_, self.scalers_, self.pcas_)])
        assert values.shape == (len(x), len(self.blocks_) * self.n_components) and np.isfinite(values).all()
        return values

    def metadata(self):
        return [dict(start=a, stop=b, samples=int(pca.n_samples_), n_components=self.n_components,
                     mean_sha256=digest(s.mean_), scale_sha256=digest(s.scale_),
                     pca_mean_sha256=digest(pca.mean_), components_sha256=digest(pca.components_),
                     explained_variance_sha256=digest(pca.explained_variance_))
                for (a, b), s, pca in zip(self.blocks_, self.scalers_, self.pcas_)]


def pipeline():
    return Pipeline([('fusion', BlockPCA()), ('clf', HistGradientBoostingClassifier(
        learning_rate=.1, min_samples_leaf=10, max_bins=63, early_stopping=False, random_state=42))])


def fit_metadata(model, x, y):
    clf = model.named_steps['clf']
    assert clf.n_iter_ == clf.max_iter and not clf.do_early_stopping_ and len(clf.classes_) == 7
    tree_fields = []
    for iteration in clf._predictors:
        assert len(iteration) == 7
        for tree in iteration:
            fields = {name: digest(tree.nodes[name]) for name in tree.nodes.dtype.names}
            fields['binned_left_cat_bitsets'] = digest(tree.binned_left_cat_bitsets)
            fields['raw_left_cat_bitsets'] = digest(tree.raw_left_cat_bitsets)
            tree_fields.append(fields)
    prob = model.predict_proba(x)
    assert np.isfinite(prob).all() and np.allclose(prob.sum(axis=1), 1)
    weights = compute_sample_weight('balanced', y) if clf.class_weight == 'balanced' else np.ones(len(y))
    return dict(fusion=model.named_steps['fusion'].metadata(), classifier=dict(
        n_iter=int(clf.n_iter_), classes=clf.classes_.tolist(), tree_fields_sha256=hashlib.sha256(
            json.dumps(tree_fields, sort_keys=True).encode()).hexdigest(),
        training_probability_sha256=digest(prob), training_weight_sha256=digest(weights)))


def load_inputs():
    assert sklearn.__version__ == '1.7.2'
    df, base, reference = inputs()
    loader = ROOT / '01_notebook/e22_caption_low/evaluate.py'
    assert sha(loader) == '2436276fd51f42a0be511c2eb354782d192a39f653bcecf3ed0b3fb70df19244'
    spec = importlib.util.spec_from_file_location('e29_pinned_caption_loader', loader)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    cap_df, full, cap_y, cap_labels, cap_folds, cap_signature = module.load_inputs()
    assert cap_df.sample_id.to_list() == df.sample_id.to_list() and np.array_equal(full[:, :3072], base)
    assert np.array_equal(cap_y, df.task2_domain_sumber.to_numpy())
    x = np.hstack([base, full[:, 4096:5120]])
    assert x.shape == (740, 4096) and np.isfinite(x).all()
    prior = ROOT / '04_hasil_eksperimen/e27_stacking/verification.json'
    assert sha(prior) == '6dd4b7b9cc8b4504d8fb6ae9d157eee33d1085f113c96a52f9dfdf30ae52e9fa'
    audit = json.loads(prior.read_text()); assert audit['status'] == 'verified' and audit['samples'] == 740 and audit['macro_f1'] < .7
    assert audit['verifier_sha256'] == sha(ROOT / '01_notebook/e27_stacking/verify.py')
    for name, value in audit['sha256'].items():
        assert sha(prior.parent / name) == value
    signature = dict(worker_sha256=sha(Path(__file__)), helper_sha256=sha(Path(__file__).with_name('e16_hierarchical.py')),
        caption_loader_sha256=sha(loader), reference=reference, caption_signature=cap_signature,
        prior_verification_sha256=sha(prior), features_sha256=digest(x), grid=GRID,
        outer='Task1 baseline5 seed42', inner='Task2 stratified3 seed42', sklearn=sklearn.__version__,
        normalization='training-only per-block StandardScaler/L2 then randomizedPCA',
        fixed=dict(pca_solver='randomized', pca_iterated_power=4, pca_power_normalizer='QR', pca_whiten=False,
                   lr=.1, min_samples_leaf=10, max_bins=63, seed=42, early_stopping=False, threads=1, search_processes=4))
    return df, x, df.task2_domain_sumber.to_numpy(), sorted(set(df.task2_domain_sumber)), list(outer(df)), signature


def selected_inner(x, y, train, options):
    scores, metadata = [], []
    splits = list(StratifiedKFold(3, shuffle=True, random_state=42).split(np.zeros(len(train)), y[train]))
    for a, b in splits:
        model = pipeline().set_params(**options).fit(x[train[a]], y[train[a]])
        pred = model.predict(x[train[b]])
        scores.append(float(f1_score(y[train[b]], pred, average='macro', zero_division=0)))
        metadata.append(fit_metadata(model, x[train[a]], y[train[a]]))
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
    parameters = list(ParameterGrid(GRID)); assert len(parameters) == 64
    predictions = np.empty(740, object); fold_ids = np.zeros(740, int)
    for k, (train, test) in enumerate(folds, 1):
        checkpoint = OUT / f'fold_{k}.json'
        if checkpoint.exists():
            record = json.loads(checkpoint.read_text())
            assert record['signature'] == signature and record['train_indices'] == train.tolist() and record['test_indices'] == test.tolist()
            assert record['sample_ids'] == df.sample_id.iloc[test].to_list()
        else:
            started = time.monotonic()
            search = GridSearchCV(pipeline(), GRID, scoring='f1_macro', n_jobs=4, error_score='raise',
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
                          selected_inner_fit=fits, outer_fit=fit_metadata(search.best_estimator_, x[train], y[train]),
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
