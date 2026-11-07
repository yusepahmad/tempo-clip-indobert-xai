"""Preparation only: deterministic LDA/PCA/prior/isolation/parallel checks."""
from e30_shrinkage_lda import *
import importlib.util
import tempfile


def main():
    started = time.monotonic(); params = list(ParameterGrid(GRID)); assert len(params) == 32
    rng = np.random.default_rng(42); x = rng.normal(size=(140, 4096)).astype(np.float32)
    y = np.asarray(['CLASS_' + str(i % 7) for i in range(140)]); y[:35] = 'CLASS_0'
    train = np.arange(112); test = np.arange(112, 140)
    for index in [0, 31]:
        model = pipeline().set_params(**params[index]).fit(x[train], y[train])
        other = pipeline().set_params(**params[index]).fit(x[train], y[train])
        assert fit_metadata(model, x[train], y[train]) == fit_metadata(other, x[train], y[train])
        assert np.array_equal(model.predict(x[test]), other.predict(x[test]))
        changed = x.copy(); changed[test] *= 100
        other = pipeline().set_params(**params[index]).fit(changed[train], y[train])
        assert fit_metadata(model, x[train], y[train]) == fit_metadata(other, changed[train], y[train])
        if params[index]['fusion__mode'] == 'semantic':
            changed = x.copy(); changed[:, 3072:] *= 100
            other = pipeline().set_params(**params[index]).fit(changed[train], y[train])
            assert fit_metadata(model, x[train], y[train]) == fit_metadata(other, changed[train], y[train])
    restricted = [{key: [value] for key, value in params[index].items()} for index in [0, 31]]
    cv = StratifiedKFold(3, shuffle=True, random_state=42)
    serial = GridSearchCV(pipeline(), restricted, scoring='f1_macro', cv=cv, n_jobs=1, error_score='raise').fit(x, y)
    parallel = GridSearchCV(pipeline(), restricted, scoring='f1_macro', cv=cv, n_jobs=4, error_score='raise').fit(x, y)
    for j in range(3):
        assert np.array_equal(serial.cv_results_[f'split{j}_test_score'], parallel.cv_results_[f'split{j}_test_score'])
    assert serial.best_params_ == parallel.best_params_
    assert fit_metadata(serial.best_estimator_, x, y) == fit_metadata(parallel.best_estimator_, x, y)
    df, real, truth, labels, folds, signature = load_inputs()
    spec = importlib.util.spec_from_file_location('e30_missing_prior_fixture', Path(__file__).with_name('e30_shrinkage_lda.py'))
    gate = importlib.util.module_from_spec(spec); spec.loader.exec_module(gate)
    with tempfile.TemporaryDirectory() as name:
        gate.ROOT = Path(name); gate.OUT = Path(name) / 'output'
        gate.load_base = lambda: (df, real, truth, labels, folds, signature['reference'])
        try:
            gate.main()
        except FileNotFoundError:
            pass
        else:
            raise AssertionError('Missing final prior must reject before output')
        assert not gate.OUT.exists()
    train, test = folds[0]; options = dict(params[-1], fusion__mode='caption_fusion', fusion__n_components=64, clf__shrinkage='auto')
    began = time.monotonic(); model = pipeline().set_params(**options).fit(real[train], truth[train]); seconds = time.monotonic() - began
    fit_metadata(model, real[train], truth[train]); prediction = model.predict(real[test])
    assert len(prediction) == 148 and set(prediction) <= set(labels)
    report = dict(status='preparation_verified', worker_sha256=sha(Path(__file__).with_name('e30_shrinkage_lda.py')),
        verifier_sha256=sha(Path(__file__).with_name('e30_shrinkage_lda_verify.py')), checks_source_sha256=sha(Path(__file__)),
        signature=signature, synthetic_samples=140, grid_points=32, expensive_fit_seconds=seconds,
        conservative_serial_seconds_520_fits_1_5_margin=seconds * 520 * 1.5, seconds_total=time.monotonic() - started,
        checks=['twoendpoints repeatfit/PCA/LDA arrays/probabilities exact', 'imbalanced training-priors vs fixeduniform',
                'heldout perturbation leaves fit unchanged; semantic mode ignores caption',
                'serial/joblib4 all6inner scores/bestparams/metadata exact', 'missing prior refuses before output',
                'actual740 currentpinnedloader/features/prior; expensive592/148 smoke without targettest score'],
        full_oof_started=False, inference_requests=0)
    target = ROOT / '04_hasil_eksperimen/e30_preparation.json'; assert not target.exists()
    save(target, report); print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    main()
