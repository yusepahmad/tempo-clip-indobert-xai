"""Audit selected inner/refit models and transforms; full grid search not rerun."""
import os
for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[key] = '1'
import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import f1_score, confusion_matrix
from sklearn.model_selection import ParameterGrid, StratifiedKFold
from e21_sparse_kernel import ROOT, OUT, GRID, load_inputs, prepare, predict, sha, save

def main():
    assert all((OUT / f'fold_{k}.json').exists() for k in range(1, 6)), 'All five folds required'
    df, x, texts, y, labels, folds, signature = load_inputs()
    assert json.loads((OUT / 'protocol.json').read_text()) == signature
    params = list(ParameterGrid(GRID)); assert len(params) == 192
    expected = np.empty(740, object); fold_ids = np.zeros(740, int); audit = []
    for k, (train, test) in enumerate(folds, 1):
        r = json.loads((OUT / f'fold_{k}.json').read_text())
        assert r['signature'] == signature and r['fold'] == k
        assert r['train_indices'] == train.tolist() and r['test_indices'] == test.tolist()
        assert r['sample_ids'] == df.sample_id.iloc[test].to_list() and r['grid_params'] == params
        scores = np.array(r['inner_fold_scores'])
        assert scores.shape == (192, 3) and np.isfinite(scores).all() and np.all((scores >= 0) & (scores <= 1))
        means = scores.mean(axis=1); best = int(np.argmax(means))
        assert r['best_index'] == best and r['best_params'] == params[best]
        assert abs(r['inner_macro_f1'] - means[best]) < 1e-12
        inner = list(StratifiedKFold(3, shuffle=True, random_state=42).split(np.zeros(len(train)), y[train]))
        reproduced = []
        for j, (a, b) in enumerate(inner):
            cache = prepare(x, texts, train[a], train[b])
            assert cache['fit'] == r['inner_fit'][j]
            pred = predict(cache, params[best], y[train[a]])
            reproduced.append(float(f1_score(y[train[b]], pred, average='macro', zero_division=0)))
        assert np.allclose(reproduced, scores[best], rtol=0, atol=1e-12)
        full = prepare(x, texts, train, test)
        assert full['fit'] == r['outer_fit'] and full['fit']['training_samples'] == 592
        pred = predict(full, params[best], y[train])
        assert pred.tolist() == r['predictions']
        expected[test] = pred; fold_ids[test] = k
        audit.append(dict(fold=k, inner_macro_f1=float(np.mean(reproduced)), params=params[best]))
        print('Verified E21 selected inner/refit/scaler/vocabulary/idf', k, flush=True)
    rows = pd.read_csv(OUT / 'oof.csv')
    assert len(rows) == 740 and rows.sample_id.is_unique
    assert rows.sample_id.to_list() == df.sample_id.to_list() and rows.truth.to_list() == y.tolist()
    assert np.array_equal(rows.fold, fold_ids) and np.array_equal(rows.prediction, expected)
    assert set(expected) <= set(labels)
    matrix = [[sum(t == a and p == b for t, p in zip(y, expected)) for b in labels] for a in labels]
    per_class = [2 * matrix[j][j] / (sum(matrix[j]) + sum(row[j] for row in matrix)) for j in range(7)]
    manual = sum(per_class) / 7
    assert abs(manual - f1_score(y, expected, average='macro', zero_division=0)) < 1e-12
    assert matrix == confusion_matrix(y, expected, labels=labels).tolist()
    report = json.loads((OUT / 'metrics.json').read_text())
    assert report['samples'] == 740 and report['signature'] == signature
    assert abs(report['macro_f1'] - manual) < 1e-12 and report['confusion_matrix'] == matrix
    assert report['oof_sha256'] == sha(OUT / 'oof.csv')
    for j, label in enumerate(labels):
        assert abs(report['classification'][label]['f1-score'] - per_class[j]) < 1e-12
    files = ['protocol.json', 'metrics.json', 'oof.csv'] + [f'fold_{k}.json' for k in range(1, 6)]
    verified = dict(status='verified', samples=740, macro_f1=manual, folds=audit,
                    verifier_sha256=sha(Path(__file__)),
                    checks=['pinned original sources; input-only text construction',
                            'all original740 IDs/truth/baseline folds',
                            '192 grid ordering/scores/argmax; chosen inner3 recomputed, full grid not rerun',
                            'all train-only numeric scalers and sparse vocabulary/idf metadata reproduced',
                            'all5 outer refits and740 predictions reproduced', 'manual7x7/per-class/macroF1'],
                    sha256={name: sha(OUT / name) for name in files})
    save(OUT / 'verification.json', verified); print(json.dumps(verified, indent=2))

if __name__ == '__main__':
    main()
