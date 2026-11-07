"""Audit final copied PCA/LDA evidence without fitting or external requests."""
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
RECOVERY = PROJECT.parent / 'docs/server-recovery/2026-10-12/e32_crop'
BASE = PROJECT.parent / 'docs/server-recovery/2026-10-10/e14_weighted_fusion'
HISTORY = PROJECT.parent / 'docs/server-recovery/2026-10-11/e23_siglip2'
GRID=dict(fusion__e5_weight=[.5,2],fusion__full_weight=[0,1],fusion__crop_weight=[0,1],
          clf__C=[1,10],clf__gamma=[.1,'scale'],clf__class_weight=[None,'balanced'])
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_text())


def rows(path):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))


def parameters():
    keys = sorted(GRID)
    result = [dict(zip(keys, values)) for values in itertools.product(*(GRID[key] for key in keys))]
    assert len(result) == 64
    return result


def first_best(scores):
    assert len(scores) == 64
    assert all(len(s) == 3 and all(type(t) in (int, float) and math.isfinite(t) and 0 <= t <= 1 for t in s) for s in scores)
    means = [sum(s) / 3 for s in scores]
    return max(range(64), key=lambda i: means[i]), means


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
    blocks=[(0,1536,options['fusion__e5_weight']),(1536,2560,1),(2560,3072,1),
            (3072,3840,options['fusion__full_weight']),(3840,4608,options['fusion__crop_weight'])]
    assert len(value['fusion'])==5
    for f,(a,b,w) in zip(value['fusion'],blocks):
        assert (f['start'],f['stop'],f['weight'])==(a,b,w)
        digest_string(f['mean_sha256']);digest_string(f['scale_sha256'])
    c=value['classifier'];assert c['classes']==labels and math.isfinite(c['gamma']) and c['gamma']>0
    for n in ['support_sha256','dual_sha256','intercept_sha256','training_decision_sha256']:digest_string(c[n])


def features():
    import runpy,zipfile
    helper=PROJECT/'01_notebook/e22_caption_low/verify_root_copy.py'
    assert sha(helper)=='086d41e070fad216f5693e0cd3dc7fd3faec406f1d6a2f445f91132aab648b6a'
    ns=runpy.run_path(str(helper));npread=ns['npy'];unit=ns['unit_error']
    out=RECOVERY/'full_features';v=read(out/'verification.json');meta=read(out/'meta.json');sig=read(out/'protocol.json')
    names=['embeddings.npz','meta.json','protocol.json','preparation.json','input_audit.jsonl']
    assert v['status']=='verified' and v['samples']==740 and v['dimension']==768 and set(v['sha256'])==set(names)
    for n,h in v['sha256'].items():assert sha(out/n)==h
    assert v['verifier_sha256']==sha(SOURCE/'verify_features.py') and sig==meta['signature']
    assert sig['worker_sha256']==sha(SOURCE/'extract.py') and sig['crop_fractions']==[.05,.12,.95,.93]
    assert sig['device']=='cpu' and sig['dtype']=='float32' and sig['threads']==8 and sig['batch']==4
    oldv=read(HISTORY/'full_features/verification.json')
    oldroot=read(HISTORY/'root_feature_verification.json')
    assert oldroot['status']=='features_verified' and oldroot['samples']==740
    assert oldroot['verification_sha256']==sha(HISTORY/'full_features/verification.json')=='ec69508ef61c5aeb74351d838576fc968e969204898b24b6a0132b517339dc10'
    prep=read(out/'preparation.json');assert prep['source_sha256']==sig['worker_sha256'] and prep['status']=='verified'
    assert prep['crop_fractions']==sig['crop_fractions'] and prep['inference_requests']==0 and prep['quality_score'] is None
    for n,h in oldv['sha256'].items():assert sha(HISTORY/'full_features'/n)==h
    assert sig['model_snapshot']==read(HISTORY/'full_features/meta.json')['signature']['model_snapshot']==read(out/'preparation.json')['model_snapshot']
    assert sig['model_snapshot']['revision']=='f775b65a79762255128c981547af89addcfe0f88'
    csvpath=PROJECT/'03_data/DATASET_740_TASK2_DOMAIN.csv'
    assert sha(csvpath)==sig['csv_sha256']=='cba20f8250bcb59481ed2d3d7d5d42fb8242c96a7ba2d11a2cd02ad80862961a'
    original=rows(csvpath);audits=[json.loads(l) for l in (out/'input_audit.jsonl').read_text().splitlines()]
    old=[json.loads(l) for l in (HISTORY/'full_features/input_audit.jsonl').read_text().splitlines()]
    assert len(original)==len(audits)==len(old)==740
    for i,(row,a,b) in enumerate(zip(original,audits,old)):
        assert a['index']==b['index']==i and a['sample_id']==b['sample_id']==row['sample_id']
        assert a['image_name']==b['image_name']==Path(row['image_path']).name
        assert a['image_sha256']==b['image_sha256']==row['image_sha256']
        w,h=a['original_size'];assert type(w)is int and type(h)is int and w>0 and h>0
        assert a['crop_box']==[int(.05*w),int(.12*h),int(.95*w),int(.93*h)]
        digest_string(a['pixel_sha256'])
    assert meta['samples']==740 and meta['dimension']==768 and meta['status']=='complete'
    assert meta['embeddings_sha256']==sha(out/'embeddings.npz') and meta['input_audit_sha256']==sha(out/'input_audit.jsonl')
    with zipfile.ZipFile(out/'embeddings.npz') as z:
        assert set(z.namelist())=={'sample_id.npy','image.npy'}
        assert all(x.file_size<10000000 for x in z.infolist())
        assert npread(z.read('sample_id.npy'),(740,))==[r['sample_id'] for r in original]
        maximum=unit(npread(z.read('image.npy'),(740,768)),740,768)
    assert v['sampled_indices']==[0,1,37,123,369,739]
    assert set(v['maximum_absolute_errors'])=={str(i) for i in v['sampled_indices']}
    assert all(math.isfinite(x) and 0<=x<=1e-5 for x in v['maximum_absolute_errors'].values())
    return dict(status='verified',samples=740,dimension=768,verification_sha256=sha(out/'verification.json'),
       verifier_sha256=sha(Path(__file__)),maximum_norm_error=maximum,
       checks=['5manifest/currentbuilder/auditor/model/E23snapshot pins','original740IDs/imageSHA/cropgeometry; E23full manifest unchanged','nonpicklefinitefloat32unit768/UnicodeIDs'],
       limitations=['root does not rerun processor or encoder; server reconstructed740pixels and sampled6forwards','root geometry uses server-recorded originaldimensions','no Task2 score'])


def audit(out):
    verified = read(out / 'verification.json'); metrics = read(out / 'metrics.json'); signature = read(out / 'protocol.json')
    assert verified['status'] == 'verified' and verified['samples'] == metrics['samples'] == 740
    names = ['protocol.json', 'metrics.json', 'oof.csv'] + [f'fold_{k}.json' for k in range(1, 6)]
    assert set(verified['sha256']) == set(names)
    for name, digest in verified['sha256'].items():
        assert sha(out / name) == digest
    assert verified['verifier_sha256'] == sha(SOURCE / 'verify.py')
    assert signature['worker_sha256'] == sha(SOURCE / 'evaluate.py')
    assert signature['reference_loader_sha256']==sha(PROJECT/'01_notebook/e23_siglip2/evaluate.py')
    assert signature['reference']['worker_sha256']==signature['reference_loader_sha256']
    assert signature['reference']['helper_sha256']==sha(PROJECT/'01_notebook/e16_hierarchical.py')
    assert signature==read(RECOVERY/'evaluator_preparation.json')['signature'] and signature['grid']==GRID
    assert signature['reference']['reference']==read(BASE/'protocol.json')
    assert signature['outer']=='Task1 baseline5 seed42' and signature['inner']=='Task2 stratified3 seed42' and signature['n_jobs']==1
    checked=features();stored=read(RECOVERY/'root_feature_verification.json');assert checked==stored
    assert signature['embedding_verification_sha256']==stored['verification_sha256']
    assert signature['embedding_meta_sha256']==sha(RECOVERY/'full_features/meta.json')
    assert signature['reference']['embedding_verification_sha256']==sha(HISTORY/'full_features/verification.json')
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
                'previously root-audited E14/E23 fullimage/crop features/currentpreparation', 'original740CSV/IDs/truth/baselinefolds',
                'five disjoint592/148 partitions cover740once', '64grid/firstargmax/selectedSVCstate/scaler metadata',
                'manual7class confusion/perclass/MacroF1'], limitations=['server auditor reproduces selectedinner/refit/scalers/crop/SVCstate/decisions/predictions; root does not fit or rerun fullgrid',
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
    print('PASS grid64/firsttie/manualF1/4invalidscores/missingfullgate; no final report')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--selftest', action='store_true');parser.add_argument('--features',action='store_true')
    args=parser.parse_args()
    if args.selftest:
        selftest()
    elif args.features:
        report=features()
        with (RECOVERY/'root_feature_verification.json').open('x') as stream:stream.write(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report,indent=2))
    else:
        report = audit(RECOVERY / 'full_oof')
        with (RECOVERY / 'root_oof_verification.json').open('x') as stream:
            stream.write(json.dumps(report, indent=2) + '\n')
        print(json.dumps(report, indent=2))
