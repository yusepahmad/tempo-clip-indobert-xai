"""Reproduce every selected nested fit using raw sparse linear/RBF SVC."""
import os
for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[key] = '1'
import json
from pathlib import Path
from evaluate import (OUT, GRID, load_inputs, raw_fit_predict, np, pd, f1_score,
                      ParameterGrid, StratifiedKFold, sha, save)


def main():
    df, semantic, texts, y, labels, folds, signature = load_inputs()
    assert json.loads((OUT / 'protocol.json').read_text()) == signature
    parameters = list(ParameterGrid(GRID))
    assert len(parameters) == 256
    expected = np.empty(740, object)
    fold_ids = np.zeros(740, int)
    audits = []
    for k, (train, test) in enumerate(folds, 1):
        r = json.loads((OUT / f'fold_{k}.json').read_text())
        assert r['signature'] == signature and r['fold'] == k
        assert r['train_indices'] == train.tolist() and r['test_indices'] == test.tolist()
        assert len(train) == 592 and len(test) == 148
        assert r['sample_ids'] == df.sample_id.iloc[test].to_list() and r['grid_params'] == parameters
        scores = np.asarray(r['inner_fold_scores'])
        assert scores.shape == (256, 3) and np.isfinite(scores).all() and np.all((scores >= 0) & (scores <= 1))
        means = scores.mean(axis=1)
        best = int(np.argmax(means))
        assert r['best_index'] == best and r['best_params'] == parameters[best]
        assert abs(r['inner_macro_f1'] - means[best]) < 1e-12
        inner = list(StratifiedKFold(3, shuffle=True, random_state=42).split(np.zeros(len(train)), y[train]))
        reproduced = []
        for j, (a, b) in enumerate(inner):
            pred, metadata, _ = raw_fit_predict(semantic, texts, train[a], train[b], parameters[best], y[train[a]])
            assert metadata == r['selected_inner_fit'][j]
            reproduced.append(float(f1_score(y[train[b]], pred, average='macro', zero_division=0)))
        assert np.allclose(reproduced, scores[best], rtol=0, atol=1e-12)
        pred, metadata, _ = raw_fit_predict(semantic, texts, train, test, parameters[best], y[train])
        assert metadata == r['outer_fit'] and pred.tolist() == r['predictions']
        expected[test] = pred
        fold_ids[test] = k
        audits.append(dict(fold=k, params=parameters[best], inner_macro_f1=float(np.mean(reproduced))))
        print('Verified selected raw sparse inner/refit/vocabulary/scalers', k, flush=True)
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
        checks=['original740 IDs/truth/baselinefold and pinned caption/features/sources',
                '256grid ordering/firstargmax; all selected inner3 scores reproduced with raw sparse SVC',
                'training-only vocabularies/IDF/scalers/outerrefits/all740 predictions reproduced',
                'manual seven-class confusion/perclass/MacroF1'],
        limitations=['full grid not rerun with raw SVC; repeated experiment selection bias remains',
                     'caption semantics not certified; upstream encoder reproduction sampled12view/sample pairs']))
    print('E26 OOF VERIFIED', score, flush=True)


if __name__ == '__main__':
    main()
