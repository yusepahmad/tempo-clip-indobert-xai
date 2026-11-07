"""Audit copied E28 OOF evidence; no fitting, model access or API requests."""
import argparse
import csv
import hashlib
import itertools
import json
import math
from pathlib import Path
import tempfile

SOURCE = Path(__file__).resolve().parent
PROJECT = SOURCE.parents[1]
RECOVERY = SOURCE.parents[2] / 'docs/server-recovery/2026-10-11/e28_mapping'
BASE = SOURCE.parents[2] / 'docs/server-recovery/2026-10-10/e14_weighted_fusion'
OPTIONS = dict(clf__C=[1, 10, 100], clf__gamma=['scale', .1, 1], clf__class_weight=[None, 'balanced'])
GRID = [dict(fusion__mode=['interpretation_only', 'interpretation_context_only'], **OPTIONS),
        dict(fusion__mode=['fusion_interpretation', 'fusion_context'], fusion__interpretation_weight=[0, .5, 1, 2],
             fusion__e5_weight=[.5, 2], fusion__clip_weight=[.5, 1], **OPTIONS)]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_text())


def rows(path):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))


def parameters():
    result = []
    for grid in GRID:
        keys = sorted(grid)
        result.extend(dict(zip(keys, values)) for values in itertools.product(*(grid[key] for key in keys)))
    assert len(result) == 612
    return result


def first_best(scores):
    assert len(scores) == 612
    assert all(len(s) == 3 and all(type(t) in (int, float) and math.isfinite(t) and 0 <= t <= 1 for t in s) for s in scores)
    means = [sum(s) / 3 for s in scores]
    return max(range(612), key=lambda i: means[i]), means


def manual_score(truth, prediction, labels):
    assert len(truth) == len(prediction) and len(labels) == 7
    assert set(truth) <= set(labels) and set(prediction) <= set(labels)
    cm = [[sum(t == a and p == b for t, p in zip(truth, prediction)) for b in labels] for a in labels]
    denominators = [sum(cm[j]) + sum(row[j] for row in cm) for j in range(7)]
    per = [2 * cm[j][j] / denominators[j] if denominators[j] else 0 for j in range(7)]
    return cm, per, sum(per) / 7


def fits(values, options):
    view = (4096, 5120) if options['fusion__mode'] in ('interpretation_context_only', 'fusion_context') else (3072, 4096)
    blocks = [(view, 1)] if options['fusion__mode'].endswith('_only') else [
        ((0, 1536), options['fusion__e5_weight']), ((1536, 2560), 1),
        ((2560, 3072), options['fusion__clip_weight']), (view, options['fusion__interpretation_weight'])]
    assert len(values) == len(blocks)
    for fit, ((a, b), weight) in zip(values, blocks):
        assert fit['start'] == a and fit['stop'] == b and fit['weight'] == weight
        for key in ('mean_sha256', 'scale_sha256'):
            assert isinstance(fit[key], str) and len(fit[key]) == 64 and all(c in '0123456789abcdef' for c in fit[key])


def audit(out):
    v = read(out / 'verification.json'); metrics = read(out / 'metrics.json'); signature = read(out / 'protocol.json')
    reference = signature['reference_signature']
    assert v['status'] == 'verified' and v['samples'] == metrics['samples'] == 740
    expected = ['protocol.json', 'metrics.json', 'oof.csv'] + [f'fold_{k}.json' for k in range(1, 6)]
    assert set(v['sha256']) == set(expected)
    for name, digest in v['sha256'].items():
        assert sha(out / name) == digest
    assert v['verifier_sha256'] == sha(SOURCE / 'verify_cached.py')
    assert signature['cached_worker_sha256'] == sha(SOURCE / 'evaluate_cached.py')
    assert reference['worker_sha256'] == sha(SOURCE / 'evaluate.py')
    assert reference['helper_sha256'] == sha(SOURCE.parent / 'e16_hierarchical.py')
    assert reference['grid'] == GRID and reference['outer'] == 'Task1 baseline5 seed42' and reference['inner'] == 'Task2 stratified3 seed42'
    assert reference['normalization'] == 'training-only per-block StandardScaler/L2 then weights' and reference['n_jobs'] == 1
    feature = RECOVERY / 'full_embeddings'
    feature_audit = read(RECOVERY / 'root_full_feature_verification.json')
    assert feature_audit['status'] == 'verified' and feature_audit['samples'] == 740
    assert feature_audit['verifier_sha256'] == sha(SOURCE / 'verify_root_copy.py')
    assert feature_audit['embedding_verification_sha256'] == reference['embedding_verification_sha256'] == sha(feature / 'verification.json')
    assert reference['embedding_meta_sha256'] == sha(feature / 'meta.json')
    for name, digest in read(feature / 'verification.json')['sha256'].items():
        assert sha(feature / name) == digest
    assert reference['reference'] == read(BASE / 'protocol.json')
    original_path = PROJECT / '03_data/DATASET_740_TASK2_DOMAIN.csv'
    assert sha(original_path) == reference['reference']['data_sha256'] == 'cba20f8250bcb59481ed2d3d7d5d42fb8242c96a7ba2d11a2cd02ad80862961a'
    original = rows(original_path); oof = rows(out / 'oof.csv'); baseline = rows(BASE / 'weighted_oof.csv')
    assert len(original) == len(oof) == len(baseline) == 740 and len({a['sample_id'] for a in oof}) == 740
    for a, b, row in zip(oof, baseline, original):
        assert a['sample_id'] == b['sample_id'] == row['sample_id']
        assert a['truth'] == b['truth'] == row['task2_domain_sumber'] and a['fold'] == b['fold']
    grid = parameters(); all_test = []
    assert len(v['folds']) == 5
    for k in range(1, 6):
        f = read(out / f'fold_{k}.json'); train = f['train_indices']; test = f['test_indices']
        assert f['signature'] == signature and f['fold'] == k and len(train) == 592 and len(test) == 148
        assert all(type(i) is int for i in train + test) and not set(train) & set(test)
        assert sorted(train + test) == list(range(740))
        assert f['sample_ids'] == [oof[i]['sample_id'] for i in test]
        assert f['predictions'] == [oof[i]['prediction'] for i in test] and all(oof[i]['fold'] == str(k) for i in test)
        assert f['grid_params'] == grid
        best, means = first_best(f['inner_fold_scores'])
        assert f['best_index'] == best and f['best_params'] == grid[best] and abs(f['inner_macro_f1'] - means[best]) < 1e-12
        audit_fold = v['folds'][k - 1]
        assert audit_fold['fold'] == k and audit_fold['params'] == grid[best] and abs(audit_fold['inner_macro_f1'] - means[best]) < 1e-12
        assert len(f['selected_inner_fit']) == 3
        for fit in [*f['selected_inner_fit'], f['outer_fit']]:
            fits(fit, grid[best])
        all_test.extend(test)
    assert sorted(all_test) == list(range(740))
    labels = sorted({a['truth'] for a in oof})
    cm, per, score = manual_score([a['truth'] for a in oof], [a['prediction'] for a in oof], labels)
    assert cm == metrics['confusion_matrix'] and abs(score - metrics['macro_f1']) < 1e-12 and abs(score - v['macro_f1']) < 1e-12
    assert metrics['signature'] == signature and metrics['oof_sha256'] == sha(out / 'oof.csv')
    for j, label in enumerate(labels):
        assert abs(per[j] - metrics['classification'][label]['f1-score']) < 1e-12
    return dict(status='verified', samples=740, macro_f1=score, server_verification_sha256=sha(out / 'verification.json'),
                verifier_sha256=sha(Path(__file__)), root_feature_verification_sha256=sha(RECOVERY / 'root_full_feature_verification.json'),
                checks=['8copied hashes/current cached/raw/verifier/helper source pins', 'previously root-audited1480features and unchanged feature hashes',
                        'original740CSV/IDs/truth/baselinefolds', 'five disjoint592/148 partitions cover740once',
                        '612exactgrid/firstargmax/allselectedfit metadata and raw-auditor means', 'manual7class confusion/perclass/MacroF1'],
                limitations=['server auditor reproduces selectedinner/refit/scalers/predictions; root does not fit models or rerun fullgrid',
                             'embedding reproduction sampled12view/sample pairs only', 'repeated experiment selection bias remains; no external holdout'])


def selftest():
    grid = parameters(); assert len(grid) == 612
    best, means = first_best([[.5] * 3 for _ in grid]); assert best == 0 and means[0] == .5
    labels = list('ABCDEFG')
    _, per, score = manual_score(labels, labels, labels); assert per == [1] * 7 and score == 1
    _, _, score = manual_score(labels, labels[1:] + labels[:1], labels); assert score == 0
    invalid = [lambda: first_best([[float('nan')] * 3 for _ in grid]),
               lambda: first_best([[1.1] * 3 for _ in grid]), lambda: first_best([[.5] * 2 for _ in grid]),
               lambda: first_best([[.5] * 3 for _ in grid[:-1]]), lambda: manual_score(labels, ['INVALID'] * 7, labels)]
    for function in invalid:
        try:
            function()
        except AssertionError:
            pass
        else:
            raise AssertionError('Invalid evidence accepted')
    with tempfile.TemporaryDirectory() as name:
        try:
            audit(Path(name))
        except FileNotFoundError:
            pass
        else:
            raise AssertionError('Missing fullOOF evidence accepted')
    print('PASS grid612,first-tie,manual7classF1,5invalid cases,missing-fullOOF gate; no report written')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--selftest', action='store_true')
    if parser.parse_args().selftest:
        selftest()
    else:
        report = audit(RECOVERY / 'full_oof_cached')
        with (RECOVERY / 'root_oof_verification.json').open('x') as stream:
            stream.write(json.dumps(report, indent=2) + '\n')
        print(json.dumps(report, indent=2))
