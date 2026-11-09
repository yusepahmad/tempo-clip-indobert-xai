"""Predeclared parity and leakage checks, with no held-out target quality selection."""
import json
from pathlib import Path
import tempfile
import evaluate as worker
from evaluate import (np, ParameterGrid, GRID, Features, prepare, projection, predict,
                      raw_fit_predict, gamma_scale, load_inputs, text_inputs, sha, save)


def parity(semantic, texts, y, train, test, indices):
    parameters = list(ParameterGrid(GRID))
    assert len(parameters) == 256
    checks = []
    for i in indices:
        options = parameters[i]
        cache = prepare(semantic, texts, train, test, options['view'], options['analyzer'])
        cached = predict(cache, options, y[train])
        raw, metadata, gamma = raw_fit_predict(semantic, texts, train, test, options, y[train])
        assert cached.tolist() == raw.tolist() and metadata == cache['metadata']
        a = projection(cache['train'], options)
        if options['kernel'] == 'rbf':
            assert abs(gamma - gamma_scale(a)) < 1e-12
        altered = semantic.copy()
        altered[test] += 1000
        altered_texts = {key: value.copy() for key, value in texts.items()}
        for key in altered_texts:
            altered_texts[key][test] = 'heldoutuniquemarker replacement new objects'
        isolated = prepare(altered, altered_texts, train, test, options['view'], options['analyzer'])
        assert cache['metadata'] == isolated['metadata']
        original_train = projection(cache['train'], options)
        isolated_train = projection(isolated['train'], options)
        assert original_train.shape == isolated_train.shape and (original_train != isolated_train).nnz == 0
        feature = Features().fit(altered, altered_texts, train, options['view'], options['analyzer'])
        assert 'heldoutuniquemarker' not in feature.vectorizers[0].vocabulary_
        if options['semantic_weight'] == 0:
            assert projection(cache['test'], options).shape == projection(isolated['test'], options).shape
            base_changed = prepare(altered, texts, train, test, options['view'], options['analyzer'])
            assert (projection(cache['test'], options) != projection(base_changed['test'], options)).nnz == 0
        checks.append(dict(index=i, options=options, samples=len(test)))
    return checks


def main():
    rng = np.random.default_rng(42)
    semantic = rng.standard_normal((70, 3072), dtype=np.float32)
    texts = dict(caption=np.asarray([f'object {i % 7} wheel water rope bird chess bridge ' + ('car ' * (i % 5 + 1)) for i in range(70)], object))
    texts['context'] = np.asarray([s + ' headline ekonomi politik pemilu konteks' for s in texts['caption']], object)
    y = np.asarray([str(i % 7) for i in range(70)])
    synthetic = parity(semantic, texts, y, np.arange(49), np.arange(49, 70), [0, 15, 32, 63, 64, 79, 128, 191, 192, 207, 240, 255])
    df, semantic, texts, y, labels, folds, signature = load_inputs()
    caption_dir = worker.ROOT / '04_hasil_eksperimen/e22_caption_low'
    captions = [json.loads(line) for line in (caption_dir / 'captions.jsonl').read_text().splitlines()]
    permuted = df.copy()
    for name in ('task2_domain_sumber', 'task1_issue'):
        permuted[name] = permuted[name].iloc[::-1].to_numpy()
    assert all(np.array_equal(text_inputs(permuted, captions)[key], value) for key, value in texts.items())
    actual = parity(semantic, texts, y, *folds[0], [0, 63, 64, 127, 192, 255])
    old_root = worker.ROOT
    try:
        with tempfile.TemporaryDirectory() as tmp:
            worker.ROOT = Path(tmp)
            try:
                load_inputs()
            except FileNotFoundError:
                pass
            else:
                raise AssertionError('missingcaptiongate failed')
    finally:
        worker.ROOT = old_root
    original_sha = worker.sha
    try:
        worker.sha = lambda path: '0' * 64 if str(path) == worker.spec.origin else original_sha(path)
        try:
            load_inputs()
        except AssertionError:
            pass
        else:
            raise AssertionError('sourcechangegate failed')
    finally:
        worker.sha = original_sha
    report = dict(status='verified', grid_size=256, worker_sha256=sha(Path(worker.__file__)),
        verifier_sha256=sha(Path(__file__).with_name('verify.py')), checks_sha256=sha(Path(__file__)),
        input_signature=signature, synthetic=synthetic, actual_fixed_fold1=actual,
        checks=['raw sparse/precomputed prediction and scaler/vocabulary/IDF/gamma parity',
                'heldout changes preserve training transforms and fit metadata',
                'heldout-only word absent from vocabulary; lexical-only ignores changed semantic',
                'original label permutation leaves text inputs unchanged; missingcaption/sourcechange gates reject'],
        limitations=['18 fixed parameters checked, not exhaustive256; no targettest quality used for selection'])
    path = worker.ROOT / '04_hasil_eksperimen/e26_caption_lexical_preparation.json'
    assert not path.exists()
    save(path, report)
    print(json.dumps(dict(status='verified', grid_size=256, synthetic=len(synthetic), actual=len(actual))), flush=True)


if __name__ == '__main__':
    main()
