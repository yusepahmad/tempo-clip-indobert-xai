"""Audit selected E17 inner fits, additive kernel and all 740 refit predictions."""
import os
for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[key] = '1'
import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.model_selection import ParameterGrid, StratifiedKFold, cross_val_score
from e17_additive_kernel import OUT, inputs, outer, pipeline, sha

report = json.loads((OUT / 'additive.json').read_text())
rows = pd.read_csv(OUT / 'additive_oof.csv')
protocol = json.loads((OUT / 'protocol.json').read_text())
assert protocol['worker_sha256'] == sha(Path(__file__).with_name('e17_additive_kernel.py'))
assert protocol['input_helper_sha256'] == sha(Path(__file__).with_name('e16_hierarchical.py'))
assert report['signature'] == protocol and report['samples'] == 740
df, x, source = inputs()
assert protocol['reference'] == source and protocol['n_jobs'] == 1
assert protocol['outer'] == 'Task1 baseline stratified5 seed42'
assert protocol['inner'] == 'Task2 stratified3 seed42'
y = df.task2_domain_sumber.to_numpy()
labels = sorted(set(y))
fold_ids = np.zeros(740, int)
predictions = np.empty(740, object)
records = []
for k, (tr, te) in enumerate(outer(df), 1):
    record = json.loads((OUT / f'fold_{k}.json').read_text())
    records.append(record)
    assert record['signature'] == protocol and record['fold'] == k
    assert record['train_indices'] == tr.tolist() and record['test_indices'] == te.tolist()
    assert record['sample_ids'] == df.sample_id.iloc[te].tolist() and not set(tr) & set(te)
    grid = record['grid_results']
    assert [r['params'] for r in grid] == list(ParameterGrid(protocol['grid']))
    assert len(grid) == 108 and all(0 <= r['mean_inner_macro_f1'] <= 1 for r in grid)
    best = max(grid, key=lambda row: row['mean_inner_macro_f1'])
    assert best['params'] == record['params'] and best['mean_inner_macro_f1'] == record['inner_macro_f1']
    model = pipeline().set_params(**record['params'])
    score = float(cross_val_score(model, x[tr], y[tr], scoring='f1_macro', n_jobs=1,
                                 cv=StratifiedKFold(3, shuffle=True, random_state=42),
                                 error_score='raise').mean())
    assert abs(score - record['inner_macro_f1']) < 1e-12
    model.fit(x[tr], y[tr])
    transformed = model.named_steps['fusion'].transform(x[tr][:24])
    head = model.named_steps['clf']
    assert len(head.train_) == len(tr)
    kernel = head.kernel(transformed, transformed)
    assert np.isfinite(kernel).all() and np.allclose(kernel, kernel.T, atol=1e-10)
    assert np.allclose(np.diag(kernel), 1, atol=1e-8)
    assert np.linalg.eigvalsh(kernel).min() >= -1e-8
    pred = model.predict(x[te])
    assert pred.tolist() == record['predictions']
    predictions[te] = pred
    fold_ids[te] = k
    print('Verified chosen inner/grid/kernel/refit fold', k, flush=True)
assert report['folds'] == records
assert len(rows) == 740 and rows.sample_id.is_unique
assert rows.sample_id.tolist() == df.sample_id.tolist() and rows.truth.tolist() == y.tolist()
assert np.array_equal(rows.fold, fold_ids) and np.array_equal(rows.prediction, predictions)
lookup = {label: i for i, label in enumerate(labels)}
matrix = np.zeros((7, 7), int)
for truth, prediction in zip(rows.truth, rows.prediction):
    matrix[lookup[truth], lookup[prediction]] += 1
scores = {}
for label, i in lookup.items():
    denominator = int(matrix[i, :].sum() + matrix[:, i].sum())
    scores[label] = 2 * int(matrix[i, i]) / denominator if denominator else 0
    assert abs(scores[label] - report['classification'][label]['f1-score']) < 1e-12
score = sum(scores.values()) / 7
assert abs(score - report['macro_f1']) < 1e-12 and matrix.tolist() == report['confusion_matrix']
verification = {'status': 'verified', 'samples': 740, 'macro_f1_manual': score,
                'per_class_f1': scores, 'verifier_sha256': sha(Path(__file__)),
                'checks': ['original data/source/frozen feature hashes and IDs',
                           'baseline outer splits and original labels',
                           'recorded full grid membership and inner argmax',
                           'chosen inner score recomputed on training only',
                           'kernel finite/symmetric/unit diagonal/subset PSD',
                           'all 740 outer-training refit predictions reproduced',
                           'manual TP/FP/FN scores and confusion matrix'],
                'sha256': {p.name: sha(p) for p in sorted(OUT.iterdir()) if p.is_file()
                           and p.name not in ('verification.json', 'run.lock') and not p.name.endswith('.tmp')}}
(OUT / 'verification.json').write_text(json.dumps(verification, indent=2) + '\n')
print(json.dumps({'status': 'verified', 'macro_f1_manual': score}, indent=2), flush=True)
