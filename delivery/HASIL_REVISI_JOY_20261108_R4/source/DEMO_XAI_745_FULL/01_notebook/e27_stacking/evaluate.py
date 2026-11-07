"""Nested, locally cross-fitted decision-score stacking of five frozen views."""
import os
for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[key] = '1'
import fcntl
import importlib.util
import json
from pathlib import Path
import sys
import time
import numpy as np
import pandas as pd
import sklearn
from sklearn.base import BaseEstimator, TransformerMixin, clone
from sklearn.ensemble import StackingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, f1_score
from sklearn.model_selection import ParameterGrid, StratifiedKFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, normalize
from sklearn.svm import SVC

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / '04_hasil_eksperimen/e27_stacking'
sys.path.append(str(ROOT / '01_notebook'))
from e16_hierarchical import sha, save
import hashlib
digest = lambda x: hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest()
GRID = dict(C=[.1, 1, 10], class_weight=[None, 'balanced'])
LOADERS = {
    'e22_caption_low': '2436276fd51f42a0be511c2eb354782d192a39f653bcecf3ed0b3fb70df19244',
    'e23_siglip2': 'de41e071e4dbdbad4cea998bf8ae4816866562e33e1da5f489eefa5b0881ef9c',
    'e25_dinov2': 'b28efd745fd5c0a0e84068ca7a1df364671e89502b2c269982dbdb6d2c1bfe52'}
BASES = [('semantic', ((0, 1536, .5), (1536, 2560, 1), (2560, 3072, 1)), .1),
         ('caption', ((3072, 4096, 1),), 'scale'),
         ('context', ((4096, 5120, 1),), 'scale'),
         ('siglip', ((5120, 5888, 1),), 'scale'),
         ('dino', ((5888, 6656, 1),), 'scale')]


def load_inputs():
    loaded = {}
    for name, expected in LOADERS.items():
        path = ROOT / '01_notebook' / name / 'evaluate.py'
        assert sha(path) == expected
        spec = importlib.util.spec_from_file_location('e27_ref_' + name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        loaded[name] = module.load_inputs()
    df, caption, y, labels, folds, caption_signature = loaded['e22_caption_low']
    for name in ('e23_siglip2', 'e25_dinov2'):
        other_df, other, other_y, other_labels, other_folds, _ = loaded[name]
        assert df.sample_id.to_list() == other_df.sample_id.to_list() and np.array_equal(y, other_y)
        assert labels == other_labels and np.array_equal(caption[:, :3072], other[:, :3072])
        assert len(folds) == len(other_folds) == 5
        for (a, b), (c, d) in zip(folds, other_folds):
            assert np.array_equal(a, c) and np.array_equal(b, d)
    x = np.hstack([caption, loaded['e23_siglip2'][1][:, 3072:], loaded['e25_dinov2'][1][:, 3072:]])
    assert x.shape == (740, 6656) and x.dtype == np.float32 and np.isfinite(x).all()
    signature = dict(worker_sha256=sha(Path(__file__)), helper_sha256=sha(ROOT / '01_notebook/e16_hierarchical.py'),
        input_signatures={name: item[-1] for name, item in loaded.items()}, features_sha256=digest(x),
        bases=json.loads(json.dumps(BASES)), base_C=1, base_class_weight='balanced', decision='ovr', grid=GRID,
        outer='original Task1 baseline5 seed42', inner='Task2 stratified3 seed42; first argmax',
        crossfit='independent Task2 stratified3 seed42 inside each current training partition',
        normalization='training-only StandardScaler/L2 per base block; training-only meta StandardScaler',
        meta='LogisticRegression lbfgs max_iter5000 random_state42',
        versions=dict(numpy=np.__version__, sklearn=sklearn.__version__), n_jobs=1)
    return df, x, y, labels, folds, signature


class IndexBlocks(TransformerMixin, BaseEstimator):
    def __init__(self, features, blocks):
        self.features = features
        self.blocks = blocks

    def fit(self, indices, y=None):
        ids = np.asarray(indices).ravel().astype(int)
        self.scalers_ = [StandardScaler().fit(self.features[ids, a:b]) for a, b, _ in self.blocks]
        return self

    def transform(self, indices):
        ids = np.asarray(indices).ravel().astype(int)
        result = np.hstack([normalize(s.transform(self.features[ids, a:b])) * w
                           for s, (a, b, w) in zip(self.scalers_, self.blocks)])
        assert np.isfinite(result).all()
        return result

    def metadata(self):
        return [dict(start=a, stop=b, weight=w, mean_sha256=digest(s.mean_), scale_sha256=digest(s.scale_))
                for s, (a, b, w) in zip(self.scalers_, self.blocks)]


def estimators(x):
    return [(name, Pipeline([('features', IndexBlocks(x, blocks)),
        ('clf', SVC(C=1, kernel='rbf', gamma=gamma, class_weight='balanced', decision_function_shape='ovr'))]))
        for name, blocks, gamma in BASES]


def base_metadata(model):
    classifier = model.named_steps['clf']
    return dict(scalers=model.named_steps['features'].metadata(), gamma=float(classifier._gamma),
                support_sha256=digest(classifier.support_), dual_sha256=digest(classifier.dual_coef_),
                intercept_sha256=digest(classifier.intercept_))


def meta_model(options):
    return Pipeline([('scale', StandardScaler()), ('clf', LogisticRegression(C=options['C'],
        class_weight=options['class_weight'], solver='lbfgs', max_iter=5000, random_state=42))])


def meta_metadata(model):
    scale = model.named_steps['scale']
    clf = model.named_steps['clf']
    assert np.all(clf.n_iter_ < 5000)
    return dict(mean_sha256=digest(scale.mean_), scale_sha256=digest(scale.scale_),
        coefficient_sha256=digest(clf.coef_), intercept_sha256=digest(clf.intercept_), iterations=clf.n_iter_.tolist())


def split_indices(y, train):
    return list(StratifiedKFold(3, shuffle=True, random_state=42).split(np.zeros(len(train)), y[train]))


def prepare(x, y, train, test):
    assert not set(train) & set(test)
    labels = sorted(set(y[train]))
    assert len(labels) == 7
    splits = split_indices(y, train)
    z_train = np.empty((len(train), 35), np.float64)
    z_test = np.empty((len(test), 35), np.float64)
    fits = []
    for i, (_, base) in enumerate(estimators(x)):
        covered = np.zeros(len(train), int)
        for a, b in splits:
            assert not set(train[a]) & set(train[b]) and not set(test) & set(train[a])
            model = clone(base).fit(train[a, None], y[train[a]])
            assert model.classes_.tolist() == labels
            z_train[b, i * 7:(i + 1) * 7] = model.decision_function(train[b, None])
            covered[b] += 1
        assert np.all(covered == 1)
        model = clone(base).fit(train[:, None], y[train])
        assert model.classes_.tolist() == labels
        z_test[:, i * 7:(i + 1) * 7] = model.decision_function(test[:, None])
        fits.append(base_metadata(model))
    assert np.isfinite(z_train).all() and np.isfinite(z_test).all()
    metadata = dict(train_meta_sha256=digest(z_train), test_meta_sha256=digest(z_test),
        full_base_fit=fits, crossfit_indices=[dict(train=train[a].tolist(), test=train[b].tolist()) for a, b in splits])
    return dict(train=z_train, test=z_test, metadata=metadata)


def predict(cache, options, y_train):
    model = meta_model(options).fit(cache['train'], y_train)
    return model.predict(cache['test']), dict(cache=cache['metadata'], meta_fit=meta_metadata(model))


def raw_predict(x, y, train, test, options):
    raw = StackingClassifier(estimators=estimators(x), final_estimator=meta_model(options),
        cv=StratifiedKFold(3, shuffle=True, random_state=42), stack_method='decision_function', n_jobs=1)
    raw.fit(train[:, None], y[train])
    # Independent sklearn cross_val_predict verifies every meta-training row.
    z_train = np.hstack([cross_val_predict(base, train[:, None], y[train],
        cv=StratifiedKFold(3, shuffle=True, random_state=42), method='decision_function', n_jobs=1)
        for _, base in estimators(x)])
    z_test = raw.transform(test[:, None])
    splits = split_indices(y, train)
    metadata = dict(train_meta_sha256=digest(z_train), test_meta_sha256=digest(z_test),
        full_base_fit=[base_metadata(model) for model in raw.estimators_],
        crossfit_indices=[dict(train=train[a].tolist(), test=train[b].tolist()) for a, b in splits])
    return raw.predict(test[:, None]), dict(cache=metadata, meta_fit=meta_metadata(raw.final_estimator_))


def main():
    df, x, y, labels, folds, signature = load_inputs()
    OUT.mkdir(exist_ok=True)
    lock = (OUT / 'run.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    protocol = OUT / 'protocol.json'
    if protocol.exists():
        assert json.loads(protocol.read_text()) == signature
    else:
        save(protocol, signature)
    parameters = list(ParameterGrid(GRID))
    assert len(parameters) == 6
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
            inner = split_indices(y, train)
            caches = [prepare(x, y, train[a], train[b]) for a, b in inner]
            scores = [[float(f1_score(y[train[b]], predict(cache, options, y[train[a]])[0], average='macro', zero_division=0))
                for (a, b), cache in zip(inner, caches)] for options in parameters]
            means = np.mean(scores, axis=1)
            best = int(np.argmax(means))
            selected_fits = [predict(cache, parameters[best], y[train[a]])[1] for (a, _), cache in zip(inner, caches)]
            pred, fit = predict(prepare(x, y, train, test), parameters[best], y[train])
            r = dict(signature=signature, fold=k, train_indices=train.tolist(), test_indices=test.tolist(),
                sample_ids=df.sample_id.iloc[test].to_list(), predictions=pred.tolist(), grid_params=parameters,
                inner_fold_scores=scores, best_index=best, best_params=parameters[best], inner_macro_f1=float(means[best]),
                selected_inner_fit=selected_fits, outer_fit=fit, seconds=time.monotonic()-started)
            save(checkpoint, r)
            print(json.dumps(dict(fold=k, params=parameters[best], inner_macro_f1=float(means[best]), seconds=r['seconds'])), flush=True)
        predictions[test] = r['predictions']
        fold_ids[test] = k
    assert set(predictions) <= set(labels)
    pd.DataFrame(dict(sample_id=df.sample_id, truth=y, prediction=predictions, fold=fold_ids)).to_csv(OUT / 'oof.csv', index=False)
    save(OUT / 'metrics.json', dict(samples=740, macro_f1=float(f1_score(y, predictions, average='macro', zero_division=0)),
        confusion_matrix=confusion_matrix(y, predictions, labels=labels).tolist(),
        classification=classification_report(y, predictions, labels=labels, output_dict=True, zero_division=0),
        signature=signature, oof_sha256=sha(OUT / 'oof.csv')))
    print('E27 OOF COMPLETE; raw StackingClassifier audit required', flush=True)


if __name__ == '__main__':
    main()
