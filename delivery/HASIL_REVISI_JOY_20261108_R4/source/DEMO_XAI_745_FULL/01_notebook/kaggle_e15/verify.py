"""Reproduce selected E15 inner/refit models, nested routing, and manual OOF scores."""
import os
for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[key] = '1'
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import LinearSVC, SVC

ROOT = Path(__file__).resolve().parents[2]
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
FAMILIES = ('last_token', 'tail_text_mean', 'last_tail', 'vlm_bge', 'vlm_visual')

def selected_pipeline(params):
    # Class repr selects a whitelisted constructor; never execute serialized text.
    name = params['clf']
    if name.startswith('SVC('):
        classifier = SVC(kernel='rbf')
        assert set(params) == {'clf', 'clf__C', 'clf__gamma', 'clf__class_weight'}
        assert float(params['clf__C']) in (1, 10, 100)
        gamma = params['clf__gamma']
        assert gamma == 'scale' or float(gamma) in (.0003, .003)
        classifier.set_params(gamma=gamma if gamma == 'scale' else float(gamma))
    elif name.startswith('LinearSVC('):
        classifier = LinearSVC(max_iter=10000, random_state=42)
        assert set(params) == {'clf', 'clf__C', 'clf__class_weight'}
        assert float(params['clf__C']) in (.01, .1, 1)
    elif name.startswith('LogisticRegression('):
        classifier = LogisticRegression(max_iter=3000)
        assert set(params) == {'clf', 'clf__C', 'clf__class_weight'}
        assert float(params['clf__C']) in (.01, .1, 1)
    else:
        raise ValueError('Classifier is outside the declared E15 grid')
    weight = params['clf__class_weight']
    assert weight in ('None', 'balanced')
    classifier.set_params(C=float(params['clf__C']), class_weight=None if weight == 'None' else weight)
    return Pipeline([('scale', StandardScaler()), ('clf', classifier)])

def count_scores(rows, labels):
    lookup = {label: i for i, label in enumerate(labels)}
    matrix = np.zeros((7, 7), int)
    for truth, prediction in zip(rows.truth, rows.prediction):
        matrix[lookup[truth], lookup[prediction]] += 1
    scores = {}
    for label, i in lookup.items():
        denominator = int(matrix[i, :].sum() + matrix[:, i].sum())
        scores[label] = 2 * int(matrix[i, i]) / denominator if denominator else 0
    return sum(scores.values()) / 7, scores, matrix.tolist()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('features', type=Path)
    feature = parser.parse_args().features
    out = ROOT / '04_hasil_eksperimen/e15_nested'
    # Demand complete output before any audit evidence is written.
    nested = json.loads((out / 'nested_selected.json').read_text())
    selected = pd.read_csv(out / 'nested_selected_oof.csv')
    feature_audit = json.loads((feature / 'verification.json').read_text())
    assert feature_audit['status'] == 'verified' and feature_audit['samples'] == 740
    assert feature_audit['verifier_sha256'] == sha(Path(__file__).with_name('verify_features.py'))
    for name, digest in feature_audit['sha256'].items():
        assert sha(feature / name) == digest
    meta = json.loads((feature / 'meta.json').read_text())
    csv = ROOT / '03_data/DATASET_740_TASK2_DOMAIN.csv'
    assert sha(csv) == meta['csv_sha256'] == 'cba20f8250bcb59481ed2d3d7d5d42fb8242c96a7ba2d11a2cd02ad80862961a'
    assert sha(Path(__file__).with_name('worker.py')) == meta['worker_sha256']
    assert sha(Path(__file__).with_name('prompt.py')) == meta['prompt_helper_sha256']
    df = pd.read_csv(csv).fillna('')
    y = df.task2_domain_sumber.to_numpy()
    labels = sorted(set(y))
    z = np.load(feature / 'embeddings.npz', allow_pickle=False)
    assert np.array_equal(z['sample_id'], df.sample_id.to_numpy())
    for key in ('last_token', 'tail_text_mean'):
        assert z[key].shape == (740, 4096) and np.isfinite(z[key]).all()
        assert np.allclose(np.linalg.norm(z[key], axis=1), 1, atol=1e-4)
    bge_path = ROOT / '04_hasil_eksperimen/e13_bge_m3/e13_bge_m3/embeddings.npz'
    clip_path = ROOT / '03_data/fitur_clip_indobert_740.npz'
    assert sha(bge_path) == 'c0d7d1fc9ac42988b0d107a694d7d3b355105f8640f776ace2617eed936495c4'
    assert sha(clip_path) == 'd27cd5dbecfffba3a8bbb96037f3181da20f1c95eb246a7d38a4627a90599e5c'
    bge = np.load(bge_path, allow_pickle=False)
    assert np.array_equal(bge['sample_id'], df.sample_id.to_numpy())
    variants = {'last_token': z['last_token'], 'tail_text_mean': z['tail_text_mean'],
                'last_tail': np.hstack([z['last_token'], z['tail_text_mean']]),
                'vlm_bge': np.hstack([z['last_token'], bge['combined']]),
                'vlm_visual': np.hstack([z['last_token'], np.load(clip_path)['img']])}
    issues = pd.Categorical(df.task1_issue, categories=sorted(set(df.task1_issue))).codes
    counts = np.bincount(issues)
    strat = np.array([i if counts[i] >= 5 else -1 for i in issues])
    folds = list(StratifiedKFold(5, shuffle=True, random_state=42).split(np.zeros(740), strat))
    fold_ids = np.zeros(740, int)
    for k, (_, te) in enumerate(folds, 1):
        fold_ids[te] = k
    evaluator_hash = sha(Path(__file__).with_name('evaluate.py'))

    def audit_rows(rows):
        assert len(rows) == 740 and rows.sample_id.is_unique
        assert rows.sample_id.tolist() == df.sample_id.tolist() and rows.truth.tolist() == y.tolist()
        assert np.array_equal(rows.fold, fold_ids) and set(rows.prediction) <= set(labels)

    reports, predictions, scores = {}, {}, {}
    for name in FAMILIES:
        report = json.loads((out / (name + '.json')).read_text())
        rows = pd.read_csv(out / (name + '_oof.csv'))
        audit_rows(rows)
        assert report['source_meta'] == meta and report['evaluator_sha256'] == evaluator_hash
        assert report['oof_sha256'] == sha(out / (name + '_oof.csv')) and len(report['folds']) == 5
        x = variants[name]
        assert np.isfinite(x).all()
        for k, (tr, te) in enumerate(folds, 1):
            record = report['folds'][k - 1]
            assert record['fold'] == k
            model = selected_pipeline(record['params'])
            inner = float(cross_val_score(model, x[tr], y[tr], scoring='f1_macro', n_jobs=1,
                                          cv=StratifiedKFold(3, shuffle=True, random_state=42),
                                          error_score='raise').mean())
            assert abs(inner - record['inner_macro_f1']) < 1e-12
            model.fit(x[tr], y[tr])
            assert np.array_equal(model.predict(x[te]), rows.prediction.iloc[te].to_numpy())
            fold_score, _, _ = count_scores(rows[rows.fold == k], labels)
            assert abs(fold_score - record['macro_f1']) < 1e-12
            print('Verified chosen inner/refit', name, k, flush=True)
        score, per_class, matrix = count_scores(rows, labels)
        assert abs(score - report['macro_f1']) < 1e-12 and matrix == report['confusion_matrix']
        for label in labels:
            assert abs(per_class[label] - report['classification'][label]['f1-score']) < 1e-12
        reports[name], predictions[name], scores[name] = report, rows, score
    audit_rows(selected)
    assert nested['source_meta'] == meta and nested['evaluator_sha256'] == evaluator_hash
    assert len(nested['selection']) == 5
    for k, record in enumerate(nested['selection'], 1):
        best = max(FAMILIES, key=lambda name: reports[name]['folds'][k - 1]['inner_macro_f1'])
        assert record == {'fold': k, 'family': best}
        assert selected[selected.fold == k].prediction.tolist() == predictions[best][predictions[best].fold == k].prediction.tolist()
    score, per_class, _ = count_scores(selected, labels)
    assert abs(score - nested['macro_f1']) < 1e-12
    for label in labels:
        assert abs(per_class[label] - nested['classification'][label]['f1-score']) < 1e-12
    verification = {'status': 'verified', 'samples': 740, 'macro_f1_manual': score,
                    'family_macro_f1_manual': scores, 'selection': nested['selection'],
                    'checks': ['input/feature/source hashes and feature audit',
                               'all six sets of original 740 IDs/labels/baseline folds',
                               'whitelisted declared classifier/parameter grid',
                               'selected inner scores recomputed on training only',
                               'all 25 final models refit and all family predictions reproduced',
                               'nested family selection/routing reconstructed',
                               'all family/fold/manual class scores and confusion matrices'],
                    'verifier_sha256': sha(Path(__file__)),
                    'feature_verification_sha256': sha(feature / 'verification.json'),
                    'sha256': {p.name: sha(p) for p in sorted(out.iterdir()) if p.is_file()
                               and p.name != 'verification.json' and not p.name.endswith('.tmp')}}
    (out / 'verification.json').write_text(json.dumps(verification, indent=2) + '\n')
    print(json.dumps({'status': 'verified', 'macro_f1_manual': score, 'family_scores': scores}, indent=2))

if __name__ == '__main__':
    main()
