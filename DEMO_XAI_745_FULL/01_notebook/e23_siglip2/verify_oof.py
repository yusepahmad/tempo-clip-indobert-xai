"""Reproduce every selected inner/refit; do not rerun the full378-grid search."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import f1_score
from sklearn.model_selection import ParameterGrid
from evaluate import OUT, GRID, load_inputs, selected_inner, pipeline, sha, save


def main():
    df, x, y, labels, folds, signature = load_inputs()
    assert json.loads((OUT / 'protocol.json').read_text()) == signature
    parameters = list(ParameterGrid(GRID)); assert len(parameters) == 378
    expected = np.empty(740, object); fold_ids = np.zeros(740, int); audits = []
    for k, (train, test) in enumerate(folds, 1):
        r = json.loads((OUT / f'fold_{k}.json').read_text())
        assert r['signature'] == signature and r['fold'] == k
        assert r['train_indices'] == train.tolist() and r['test_indices'] == test.tolist()
        assert len(train) == 592 and len(test) == 148
        assert r['sample_ids'] == df.sample_id.iloc[test].to_list() and r['grid_params'] == parameters
        scores = np.asarray(r['inner_fold_scores'])
        assert scores.shape == (378, 3) and np.isfinite(scores).all() and np.all((scores >= 0) & (scores <= 1))
        means = scores.mean(axis=1); best = int(np.argmax(means))
        assert r['best_index'] == best and r['best_params'] == parameters[best]
        assert abs(r['inner_macro_f1'] - means[best]) < 1e-12
        reproduced, fits = selected_inner(x, y, train, parameters[best])
        assert fits == r['selected_inner_fit'] and np.allclose(reproduced, scores[best], rtol=0, atol=1e-12)
        model = pipeline().set_params(**parameters[best]).fit(x[train], y[train])
        assert model.named_steps['fusion'].metadata() == r['outer_fit']
        pred = model.predict(x[test]); assert pred.tolist() == r['predictions']
        expected[test] = pred; fold_ids[test] = k
        audits.append(dict(fold=k, params=parameters[best], inner_macro_f1=float(np.mean(reproduced))))
        print('Verified selected inner/refit/scalers', k, flush=True)
    rows = pd.read_csv(OUT / 'oof.csv')
    assert len(rows) == 740 and rows.sample_id.is_unique and rows.sample_id.to_list() == df.sample_id.to_list()
    assert rows.truth.to_list() == y.tolist() and np.array_equal(rows.fold, fold_ids)
    assert rows.prediction.to_list() == expected.tolist() and set(expected) <= set(labels)
    cm = [[sum(t == a and p == b for t, p in zip(y, expected)) for b in labels] for a in labels]
    per_class = [2 * cm[j][j] / (sum(cm[j]) + sum(row[j] for row in cm)) for j in range(7)]
    score = sum(per_class) / 7
    metrics = json.loads((OUT / 'metrics.json').read_text())
    assert metrics['samples'] == 740 and metrics['signature'] == signature
    assert cm == metrics['confusion_matrix'] and abs(score - metrics['macro_f1']) < 1e-12
    assert abs(score - f1_score(y, expected, average='macro', zero_division=0)) < 1e-12
    assert metrics['oof_sha256'] == sha(OUT / 'oof.csv')
    for j, label in enumerate(labels):
        assert abs(metrics['classification'][label]['f1-score'] - per_class[j]) < 1e-12
    files = ['protocol.json', 'metrics.json', 'oof.csv'] + [f'fold_{k}.json' for k in range(1, 6)]
    save(OUT / 'verification.json', dict(status='verified', samples=740, macro_f1=score, folds=audits,
         verifier_sha256=sha(Path(__file__)), sha256={name: sha(OUT / name) for name in files},
         checks=['original740 IDs/truth/baselinefold and pinned inputs/model/sources',
                 '378grid ordering/firstargmax and all selectedinner3 scores reproduced',
                 'all training-only scaler metadata/outerrefits/740 predictions reproduced',
                 'manual seven-class confusion/perclass/MacroF1'],
         limitations=['full grid not rerun; embeddings reproduced only on predeclared6 samples',
                      'repeated experiment selection bias remains']))
    print('OOF VERIFIED', score, flush=True)


if __name__ == '__main__':
    main()
