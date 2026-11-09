"""CPU preparation only: reproducibility/isolation and worst fixed-parameter runtime."""
from e29_pca_boosting import *
import tempfile
from sklearn.base import clone
from sklearn.utils.class_weight import compute_sample_weight


def main():
    started = time.monotonic()
    parameters = list(ParameterGrid(GRID)); assert len(parameters) == 64
    rng = np.random.default_rng(42)
    x = rng.normal(size=(140, 4096)).astype(np.float32)
    y = np.asarray(['CLASS_' + str(i % 7) for i in range(140)])
    train = np.arange(112); test = np.arange(112, 140)
    for index in [0, 63]:
        options = parameters[index]
        first = pipeline().set_params(**options).fit(x[train], y[train])
        second = pipeline().set_params(**options).fit(x[train], y[train])
        assert fit_metadata(first, x[train], y[train]) == fit_metadata(second, x[train], y[train])
        assert np.array_equal(first.predict(x[test]), second.predict(x[test]))
        changed = x.copy(); changed[test] *= 100
        repeated = pipeline().set_params(**options).fit(changed[train], y[train])
        assert fit_metadata(first, x[train], y[train]) == fit_metadata(repeated, changed[train], y[train])
        assert first.named_steps['clf'].n_iter_ == options['clf__max_iter']
        nblocks = 3 if options['fusion__mode'] == 'semantic' else 4
        assert len(first.named_steps['fusion'].metadata()) == nblocks
        assert all(m['samples'] == len(train) for m in first.named_steps['fusion'].metadata())
        weights = compute_sample_weight('balanced', y[train]) if options['clf__class_weight'] == 'balanced' else np.ones(len(train))
        assert fit_metadata(first, x[train], y[train])['classifier']['training_weight_sha256'] == digest(weights)
    # Explicitly imbalanced training-only weight fixture.
    imbalanced = y[train].copy(); imbalanced[:40] = 'CLASS_0'
    options = dict(parameters[0], clf__class_weight='balanced')
    model = pipeline().set_params(**options).fit(x[train], imbalanced)
    assert fit_metadata(model, x[train], imbalanced)['classifier']['training_weight_sha256'] == digest(compute_sample_weight('balanced', imbalanced))
    fixed = [parameters[i] for i in [0, 31, 63]]
    restricted = [{key: [value] for key, value in options.items()} for options in fixed]
    split = StratifiedKFold(3, shuffle=True, random_state=42)
    serial = GridSearchCV(pipeline(), restricted, scoring='f1_macro', cv=split, n_jobs=1, error_score='raise').fit(x, y)
    parallel = GridSearchCV(pipeline(), restricted, scoring='f1_macro', cv=split, n_jobs=4, error_score='raise').fit(x, y)
    for j in range(3):
        assert np.array_equal(serial.cv_results_[f'split{j}_test_score'], parallel.cv_results_[f'split{j}_test_score'])
    assert serial.best_params_ == parallel.best_params_
    assert fit_metadata(serial.best_estimator_, x, y) == fit_metadata(parallel.best_estimator_, x, y)
    df, real, truth, labels, folds, signature = load_inputs()
    original_root = globals()['ROOT']
    # Independent import allows gate fixtures without affecting the active module.
    spec = importlib.util.spec_from_file_location('e29_gate_fixture', Path(__file__).with_name('e29_pca_boosting.py'))
    gate = importlib.util.module_from_spec(spec); spec.loader.exec_module(gate)
    with tempfile.TemporaryDirectory() as name:
        gate.ROOT = Path(name); gate.OUT = Path(name) / 'output'
        gate.inputs = lambda: (df, real[:, :3072], signature['reference'])
        try:
            gate.main()
        except FileNotFoundError:
            pass
        else:
            raise AssertionError('Missing pinned loader must reject before output')
        assert not gate.OUT.exists()
    train, test = folds[0]
    # Fixed expensive endpoint; no targettest F1 computed or used for tuning.
    expensive = dict(parameters[-1], fusion__mode='caption_fusion')
    began = time.monotonic(); model = pipeline().set_params(**expensive).fit(real[train], truth[train])
    seconds = time.monotonic() - began
    metadata = fit_metadata(model, real[train], truth[train]); prediction = model.predict(real[test])
    assert len(prediction) == 148 and set(prediction) <= set(labels)
    assert metadata['classifier']['n_iter'] == 300 and len(metadata['fusion']) == 4
    report = dict(status='preparation_verified', worker_sha256=sha(Path(__file__).with_name('e29_pca_boosting.py')),
        verifier_sha256=sha(Path(__file__).with_name('e29_pca_boosting_verify.py')), checks_source_sha256=sha(Path(__file__)),
        signature=signature, synthetic_samples=140, grid_points=64, expensive_fit_seconds=seconds,
        conservative_serial_seconds_1000_fits_1_5_margin=seconds * 1000 * 1.5,
        seconds_total=time.monotonic() - started,
        checks=['mode/component endpoints deterministic repeat/scaler/PCA/treefield/probability metadata',
                'heldout perturbation leaves training fit unchanged', 'imbalanced training-only weights',
                'fixed100/300iterations and finite normalized probabilities', 'serial/joblib4 exact all9inner scores/bestparameter/selectedfit metadata', 'missing loader gate rejects before output',
                'actual740 inputs/current prior/source/model/feature pins; expensive592/148 smoke without targettest score'],
        full_oof_started=False, inference_requests=0)
    target = ROOT / '04_hasil_eksperimen/e29_preparation.json'
    assert not target.exists(), 'Inspect prior preparation; no automatic overwrite'
    save(target, report); print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    main()
