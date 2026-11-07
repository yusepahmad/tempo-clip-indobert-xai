"""Fixed-parameter raw stacking parity and local cross-fitting leakage checks."""
import json
from pathlib import Path
import tempfile
import evaluate as worker
from evaluate import np, GRID, ParameterGrid, prepare, predict, raw_predict, load_inputs, sha, save


def checks(x, y, train, test, parameter_indices):
    parameters = list(ParameterGrid(GRID))
    assert len(parameters) == 6
    cache = prepare(x, y, train, test)
    assert cache['train'].shape == (len(train), 35) and cache['test'].shape == (len(test), 35)
    coverage = []
    for fold in cache['metadata']['crossfit_indices']:
        a, b = fold['train'], fold['test']
        assert not set(a) & set(b) and sorted(a + b) == sorted(train.tolist())
        assert not set(a) & set(test) and not set(b) & set(test)
        coverage += b
    assert sorted(coverage) == sorted(train.tolist())
    verified = []
    for index in parameter_indices:
        options = parameters[index]
        pred, metadata = predict(cache, options, y[train])
        raw, raw_metadata = raw_predict(x, y, train, test, options)
        assert raw.tolist() == pred.tolist() and raw_metadata == metadata
        verified.append(dict(index=index, options=options, samples=len(test)))
    altered_x = x.copy()
    altered_x[test] += 1000
    altered_y = y.copy()
    altered_y[test] = altered_y[test][::-1]
    altered = prepare(altered_x, altered_y, train, test)
    assert np.array_equal(cache['train'], altered['train'])
    for name in ('train_meta_sha256', 'full_base_fit', 'crossfit_indices'):
        assert cache['metadata'][name] == altered['metadata'][name]
    for index in parameter_indices:
        options = parameters[index]
        assert predict(cache, options, y[train])[1]['meta_fit'] == predict(altered, options, altered_y[train])[1]['meta_fit']
    return verified


def main():
    rng = np.random.default_rng(42)
    x = rng.standard_normal((70, 6656), dtype=np.float32)
    y = np.asarray([str(i % 7) for i in range(70)])
    synthetic = checks(x, y, np.arange(49), np.arange(49, 70), [0, 5])
    df, x, y, labels, folds, signature = load_inputs()
    actual = checks(x, y, *folds[0], [0, 5])
    old_root = worker.ROOT
    try:
        with tempfile.TemporaryDirectory() as tmp:
            worker.ROOT = Path(tmp)
            try:
                load_inputs()
            except FileNotFoundError:
                pass
            else:
                raise AssertionError('missingfeaturegate failed')
    finally:
        worker.ROOT = old_root
    original_sha = worker.sha
    try:
        worker.sha = lambda path: '0' * 64
        try:
            load_inputs()
        except AssertionError:
            pass
        else:
            raise AssertionError('sourcechangegate failed')
    finally:
        worker.sha = original_sha
    path = worker.ROOT / '04_hasil_eksperimen/e27_stacking_preparation.json'
    assert not path.exists()
    save(path, dict(status='verified', grid_size=6, worker_sha256=sha(Path(worker.__file__)),
        verifier_sha256=sha(Path(__file__).with_name('verify.py')), checks_sha256=sha(Path(__file__)),
        input_signature=signature, synthetic=synthetic, actual_fixed_fold1=actual,
        checks=['raw StackingClassifier and independent cross_val_predict exactly match predictions/all metadata',
                'three crossfit partitions cover current training once and exclude its heldout',
                'heldout feature/label changes preserve base fits, meta-training35dim and meta fits',
                'missingfeature and sourcechange gates reject'],
        limitations=['four fixed fixture/parameter cases, not exhaustive grid6; no targettest quality selection']))
    print(json.dumps(dict(status='verified', grid_size=6, synthetic=len(synthetic), actual=len(actual))), flush=True)


if __name__ == '__main__':
    main()
