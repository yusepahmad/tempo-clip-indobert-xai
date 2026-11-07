"""Audit final copied PCA/adapter evidence without fitting or external requests."""
import argparse
import csv
import hashlib
import itertools
import json
import math
from pathlib import Path
import tempfile

SOURCE = Path(__file__).resolve().parent
PROJECT = SOURCE.parent
RECOVERY = SOURCE.parents[1] / 'docs/server-recovery/2026-10-12/e31_adapter'
BASE = SOURCE.parents[1] / 'docs/server-recovery/2026-10-10/e14_weighted_fusion'
HISTORY = SOURCE.parents[1] / 'docs/server-recovery/2026-10-11'
GRID = dict(fusion__mode=['semantic', 'caption_fusion'], fusion__n_components=[64],
            clf__alpha=[0, .2], clf__weight_decay=[.01, .1], clf__class_weight=[None, 'balanced'])
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_text())


def rows(path):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))


def parameters():
    keys = sorted(GRID)
    result = [dict(zip(keys, values)) for values in itertools.product(*(GRID[key] for key in keys))]
    assert len(result) == 16
    return result


def first_best(scores):
    assert len(scores) == 16
    assert all(len(s) == 3 and all(type(t) in (int, float) and math.isfinite(t) and 0 <= t <= 1 for t in s) for s in scores)
    means = [sum(s) / 3 for s in scores]
    return max(range(16), key=lambda i: means[i]), means


def manual_score(truth, prediction, labels):
    assert len(truth) == len(prediction) and len(labels) == 7
    assert set(truth) <= set(labels) and set(prediction) <= set(labels)
    cm = [[sum(t == a and p == b for t, p in zip(truth, prediction)) for b in labels] for a in labels]
    denominators = [sum(cm[j]) + sum(row[j] for row in cm) for j in range(7)]
    per = [2 * cm[j][j] / denominators[j] if denominators[j] else 0 for j in range(7)]
    return cm, per, sum(per) / 7


def digest_string(value):
    assert isinstance(value, str) and len(value) == 64 and all(c in '0123456789abcdef' for c in value)


def fit_metadata(value, options, samples, labels):
    blocks = [(0, 1536), (1536, 2560), (2560, 3072)]
    if options['fusion__mode'] == 'caption_fusion':
        blocks.append((3072, 4096))
    assert len(value['fusion']) == len(blocks)
    for fit, (a, b) in zip(value['fusion'], blocks):
        assert fit['start'] == a and fit['stop'] == b and fit['samples'] == samples
        assert fit['n_components'] == options['fusion__n_components']
        for name in ('mean_sha256', 'scale_sha256', 'pca_mean_sha256', 'components_sha256', 'explained_variance_sha256'):
            digest_string(fit[name])
    clf = value['classifier']; assert clf['classes'] == labels
    assert clf['samples']==samples and clf['epochs']==200 and clf['dimension']==len(blocks)*64
    assert clf['alpha']==options['clf__alpha']
    assert set(clf['state_sha256'])=={'adapter.0.weight','adapter.0.bias','adapter.2.weight','adapter.2.bias','head.weight','head.bias'}
    for v in clf['state_sha256'].values():digest_string(v)
    for name in ['normalizer_mean_sha256','normalizer_scale_sha256','training_probability_sha256']:digest_string(clf[name])
    assert len(clf['loss_endpoints'])==2 and all(math.isfinite(v) and v>=0 for v in clf['loss_endpoints'])
    assert len(clf['class_weights'])==7 and all(math.isfinite(v) and v>0 for v in clf['class_weights'])
    if options['clf__class_weight'] is None:assert clf['class_weights']==[1]*7


def audit(out):
    verified = read(out / 'verification.json'); metrics = read(out / 'metrics.json'); signature = read(out / 'protocol.json')
    assert verified['status'] == 'verified' and verified['samples'] == metrics['samples'] == 740
    names = ['protocol.json', 'metrics.json', 'oof.csv'] + [f'fold_{k}.json' for k in range(1, 6)]
    assert set(verified['sha256']) == set(names)
    for name, digest in verified['sha256'].items():
        assert sha(out / name) == digest
    assert verified['verifier_sha256'] == sha(SOURCE / 'e31_adapter_verify.py')
    assert signature['worker_sha256'] == sha(SOURCE / 'e31_adapter.py')
    assert signature['transformation_loader_sha256'] == sha(SOURCE / 'e29_pca_boosting.py')
    assert signature['reference']['helper_sha256'] == sha(SOURCE / 'e16_hierarchical.py')
    assert signature['reference']['caption_loader_sha256'] == sha(SOURCE / 'e22_caption_low/evaluate.py')
    assert signature == read(RECOVERY / 'e31_preparation.json')['signature']
    assert signature['reference']['reference'] == read(BASE / 'protocol.json') and signature['grid'] == GRID
    assert signature['outer'] == 'Task1 baseline5 seed42' and signature['inner'] == 'Task2 stratified3 seed42'
    assert signature['fixed']['search_processes'] == 4 and signature['fixed']['threads'] == 1 and signature['fixed']['epochs'] == 200 and signature['fixed']['bottleneck'] == 32 and signature['fixed']['lr'] == .01
    e22 = HISTORY / 'e22_caption'; feature_audit = read(e22 / 'root_full_feature_verification.json')
    assert feature_audit['status'] == 'verified' and feature_audit['samples'] == 740
    assert signature['reference']['caption_signature']['embedding_verification_sha256'] == feature_audit['embedding_verification_sha256'] == sha(e22 / 'full_embeddings/verification.json')
    assert signature['reference']['caption_signature']['embedding_meta_sha256'] == sha(e22 / 'full_embeddings/meta.json')
    for name, digest in read(e22 / 'full_embeddings/verification.json')['sha256'].items():
        assert sha(e22 / 'full_embeddings' / name) == digest
    assert signature['prior_verification_sha256'] == sha(HISTORY / 'e30_shrinkage_lda/full_oof/verification.json')
    original_path = PROJECT / '03_data/DATASET_740_TASK2_DOMAIN.csv'
    assert sha(original_path) == signature['reference']['reference']['data_sha256'] == 'cba20f8250bcb59481ed2d3d7d5d42fb8242c96a7ba2d11a2cd02ad80862961a'
    original = rows(original_path); oof = rows(out / 'oof.csv'); baseline = rows(BASE / 'weighted_oof.csv')
    assert len(original) == len(oof) == len(baseline) == 740 and len({a['sample_id'] for a in oof}) == 740
    for a, b, row in zip(oof, baseline, original):
        assert a['sample_id'] == b['sample_id'] == row['sample_id'] and a['truth'] == b['truth'] == row['task2_domain_sumber']
        assert a['fold'] == b['fold']
    labels = sorted({r['truth'] for r in oof}); assert len(labels) == 7
    grid = parameters(); all_test = []; assert len(verified['folds']) == 5
    for k in range(1, 6):
        f = read(out / f'fold_{k}.json'); train = f['train_indices']; test = f['test_indices']
        assert f['signature'] == signature and f['fold'] == k and len(train) == 592 and len(test) == 148
        assert all(type(i) is int for i in train + test) and not set(train) & set(test) and sorted(train + test) == list(range(740))
        assert f['sample_ids'] == [oof[i]['sample_id'] for i in test] and f['predictions'] == [oof[i]['prediction'] for i in test]
        assert all(oof[i]['fold'] == str(k) for i in test) and f['grid_params'] == grid
        best, means = first_best(f['inner_fold_scores'])
        assert f['best_index'] == best and f['best_params'] == grid[best] and abs(f['inner_macro_f1'] - means[best]) < 1e-12
        server_fold = verified['folds'][k - 1]
        assert server_fold['fold'] == k and server_fold['params'] == grid[best] and abs(server_fold['inner_macro_f1'] - means[best]) < 1e-12
        assert len(f['selected_inner_fit']) == 3
        for value, count in zip(f['selected_inner_fit'], [394, 395, 395]):
            fit_metadata(value, grid[best], count, labels)
        fit_metadata(f['outer_fit'], grid[best], 592, labels); all_test.extend(test)
    assert sorted(all_test) == list(range(740))
    cm, per, score = manual_score([a['truth'] for a in oof], [a['prediction'] for a in oof], labels)
    assert cm == metrics['confusion_matrix'] and abs(score - metrics['macro_f1']) < 1e-12 and abs(score - verified['macro_f1']) < 1e-12
    assert metrics['signature'] == signature and metrics['oof_sha256'] == sha(out / 'oof.csv')
    for j, label in enumerate(labels):
        assert abs(per[j] - metrics['classification'][label]['f1-score']) < 1e-12
    return dict(status='verified', samples=740, macro_f1=score, server_verification_sha256=sha(out / 'verification.json'),
                verifier_sha256=sha(Path(__file__)), checks=['8copied hashes/current worker/auditor/helper/input/source pins',
                'previously root-audited E14/E22 frozen features/currentpreparation', 'original740CSV/IDs/truth/baselinefolds',
                'five disjoint592/148 partitions cover740once', '16grid/firstargmax/selectedPCA samplecounts/adapterstate/normalizer/classweights',
                'manual7class confusion/perclass/MacroF1'], limitations=['server auditor reproduces selectedinner/refit/scalers/PCA/adapter learnedpriors/arrays/predictions; root does not fit or rerun fullgrid',
                'upstream embedding reproduction sampled only', 'repeated experiment selection bias remains; no external holdout'])


def selftest():
    grid = parameters(); best, means = first_best([[.5] * 3 for _ in grid]); assert best == 0 and means[0] == .5
    labels = list('ABCDEFG'); assert manual_score(labels, labels, labels)[2] == 1
    assert manual_score(labels, labels[1:] + labels[:1], labels)[2] == 0
    for scores in ([[float('nan')] * 3 for _ in grid], [[1.1] * 3 for _ in grid], [[.5] * 2 for _ in grid], [[.5] * 3 for _ in grid[:-1]]):
        try:
            first_best(scores)
        except AssertionError:
            pass
        else:
            raise AssertionError('Invalid scores accepted')
    with tempfile.TemporaryDirectory() as name:
        try:
            audit(Path(name))
        except FileNotFoundError:
            pass
        else:
            raise AssertionError('Missing fullOOF gate accepted')
    print('PASS grid16/firsttie/manualF1/4invalidscores/missingfullgate; no final report')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--selftest', action='store_true')
    if parser.parse_args().selftest:
        selftest()
    else:
        report = audit(RECOVERY / 'full_oof')
        with (RECOVERY / 'root_oof_verification.json').open('x') as stream:
            stream.write(json.dumps(report, indent=2) + '\n')
        print(json.dumps(report, indent=2))
