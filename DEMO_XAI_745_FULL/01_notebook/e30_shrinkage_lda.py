"""Nested generative shrinkage LDA, training-only PCA and audited frozen inputs."""
import os
for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[key] = '1'
from pathlib import Path
import hashlib
# Verify the immutable transformation/loader before importing it.
PINNED = Path(__file__).with_name('e29_pca_boosting.py')
assert hashlib.sha256(PINNED.read_bytes()).hexdigest() == '7eea9c1ec7f491353f1f64408eb258e7782b1fe49200872f3d8c14cf192cbeb8'
from e29_pca_boosting import *
from e29_pca_boosting import load_inputs as load_base
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis

OUT = ROOT / '04_hasil_eksperimen/e30_shrinkage_lda'
GRID = dict(fusion__mode=['semantic', 'caption_fusion'], fusion__n_components=[32, 64],
            clf__shrinkage=[.01, .1, .5, 'auto'], clf__priors=[None, [1 / 7] * 7])


def pipeline():
    return Pipeline([('fusion', BlockPCA()), ('clf', LinearDiscriminantAnalysis(solver='lsqr', store_covariance=True))])


def fit_metadata(model, x, y):
    clf = model.named_steps['clf']; assert len(clf.classes_) == 7
    arrays = dict(means=clf.means_, covariance=clf.covariance_, coefficients=clf.coef_, intercept=clf.intercept_, priors=clf.priors_)
    assert all(np.isfinite(a).all() for a in arrays.values())
    expected = (np.asarray([sum(y == label) for label in clf.classes_], dtype=clf.priors_.dtype) / float(len(y))
                if clf.priors is None else np.asarray([1 / 7] * 7, dtype=clf.priors_.dtype))
    assert np.array_equal(clf.priors_, expected)
    prob = model.predict_proba(x)
    assert np.isfinite(prob).all() and np.allclose(prob.sum(axis=1), 1)
    return dict(fusion=model.named_steps['fusion'].metadata(), classifier=dict(classes=clf.classes_.tolist(),
                array_sha256={name: digest(value) for name, value in arrays.items()},
                priors=clf.priors_.tolist(), training_probability_sha256=digest(prob)))


def load_inputs():
    df, x, y, labels, folds, reference = load_base()
    prior = ROOT / '04_hasil_eksperimen/e29_pca_boosting/verification.json'
    assert sha(prior) == '523d2b9aa775d92c64839f0b76124b4eba5d3d40bd5f4fdd97d38d6609edb5df'
    audit = json.loads(prior.read_text()); assert audit['status'] == 'verified' and audit['samples'] == 740 and audit['macro_f1'] < .7
    assert audit['verifier_sha256'] == sha(Path(__file__).with_name('e29_pca_boosting_verify.py'))
    for name, value in audit['sha256'].items():
        assert sha(prior.parent / name) == value
    signature = dict(worker_sha256=sha(Path(__file__)), transformation_loader_sha256=sha(PINNED), reference=reference,
        prior_verification_sha256=sha(prior), features_sha256=digest(x), grid=GRID,
        outer='Task1 baseline5 seed42', inner='Task2 stratified3 seed42', sklearn=sklearn.__version__,
        fixed=dict(solver='lsqr', store_covariance=True, search_processes=4, threads=1))
    return df, x, y, labels, folds, signature


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
    parameters = list(ParameterGrid(GRID)); assert len(parameters) == 32
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
