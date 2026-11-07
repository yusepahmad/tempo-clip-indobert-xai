"""Independent artifact verification for decoder OOF and inner-only QLoRA pilot."""
import csv
import hashlib
import json
from pathlib import Path

import numpy as np
from sklearn.metrics import accuracy_score, f1_score

import run_micro_e12_structured_decoder as e12


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text())


def csv_rows(path):
    with path.open(newline='', encoding='utf-8-sig') as handle:
        return list(csv.DictReader(handle))


def verify_e12():
    folder = e12.OUT
    if not (folder/'result.json').exists():
        return {'status':'not_complete'}
    result = load(folder/'result.json')
    rows = csv_rows(folder/'predictions.csv')
    controls = csv_rows(folder/'control_predictions.csv')
    data = {r['sample_id']:r for r in csv_rows(e12.e10.DATA)}
    folds = {r['sample_id']:int(r['fold']) for r in csv_rows(e12.e10.FOLDS)}
    assert len(rows) == len({r['sample_id'] for r in rows}) == 740
    assert {r['sample_id'] for r in rows} == set(data)
    assert [r['sample_id'] for r in rows] == [r['sample_id'] for r in controls]
    for r in rows + controls:
        assert int(r['fold']) == folds[r['sample_id']]
        for task in e12.TASKS:
            assert r[task+'_truth'] == data[r['sample_id']][task]
    for task in e12.TASKS:
        truth = [r[task+'_truth'] for r in rows]
        predicted = [r[task+'_pred'] for r in rows]
        micro = f1_score(truth, predicted, average='micro')
        assert abs(micro - accuracy_score(truth,predicted)) < 1e-12
        assert abs(micro - result['micro_f1'][task]) < 1e-12
        assert abs(f1_score(truth,predicted,average='macro')-result['macro_f1_diagnostic'][task]) < 1e-12
        assert abs(accuracy_score(truth,[r[task+'_pred'] for r in controls])-result['control_micro_f1'][task]) < 1e-12
    audits = load(folder/'split_audit.json')
    assert len(audits) == 15
    for audit in audits:
        a, b, test = map(set, (audit['train_ids'], audit['validation_ids'], audit['outer_test_ids']))
        assert not a&b and not a&test and not b&test
        assert a|b|test == set(data)
        assert test == {sample_id for sample_id,fold in folds.items() if fold==audit['outer_fold']}
    for detail in result['fold_details']:
        chosen = max(detail['candidates'], key=lambda r:(r['minimum'],r['mean'],-r['config']['strength']))
        assert detail['selected']==chosen
        subset=[r for r in rows if int(r['fold'])==detail['fold']]
        for task in e12.TASKS:
            assert abs(accuracy_score([r[task+'_truth'] for r in subset],[r[task+'_pred'] for r in subset])-detail['outer_micro_f1'][task])<1e-12
    config=load(folder/'config.json')
    assert config['source_sha256']==sha(Path(e12.__file__))
    assert config['dataset_sha256']==sha(e12.e10.DATA)
    assert config['folds_sha256']==sha(e12.e10.FOLDS)
    for relative, expected in config['feature_sha256'].items():
        assert sha(e12.e10.ROOT/relative)==expected,relative
    assert result['predictions_sha256']==sha(folder/'predictions.csv')
    record={'status':'verified','samples':740,'outer_folds':5,'inner_audits':15,
            'checks':['dataset truth','unique IDs','fixed outer folds','micro equals accuracy',
                      'reported micro and macro','control metrics','three-way split disjointness',
                      'inner-only selection rule','source and prediction hashes'],
            'micro_f1':result['micro_f1'],'target_reached':min(result['micro_f1'].values())>=.70}
    e12.write_json(folder/'verification.json',record)
    return record


def verify_e13():
    folder=e12.OUT.parent/'MICRO_E13_joint_qlora_inner_pilot'
    control=load(folder/'control.json')
    if not (folder/'result.json').exists():
        return {'status':'awaiting_kaggle','control_micro_f1':control['validation_micro_f1']}
    result=load(folder/'result.json')
    selected=max(result['history'], key=lambda r:(r['minimum'],r['mean']))
    assert selected['epoch']==result['selected_epoch']
    assert selected['validation_micro_f1']==result['validation_micro_f1']
    assert not result['eligible_as_oof'] and not result['outer_test_evaluated']
    a,b,c=map(set,(result['split']['inner_train_ids'],result['split']['inner_validation_ids'],result['split']['untouched_outer_test_ids']))
    assert not a&b and not a&c and not b&c and len(a)==473 and len(b)==119 and len(c)==148
    assert a==set(control['inner_train_ids']) and b==set(control['validation_ids']) and c==set(control['untouched_outer_test_ids'])
    data={r['sample_id']:r for r in csv_rows(e12.e10.DATA)}
    rows=csv_rows(folder/'validation_predictions.csv')
    assert len(rows)==len({r['sample_id'] for r in rows})==119
    assert {r['sample_id'] for r in rows}==b
    metrics={}
    for task in e12.TASKS:
        assert all(r[task+'_truth']==data[r['sample_id']][task] for r in rows)
        metrics[task]=float(f1_score([r[task+'_truth'] for r in rows],[r[task+'_pred'] for r in rows],average='micro'))
        assert abs(metrics[task]-result['validation_micro_f1'][task])<1e-12
        macro=float(f1_score([r[task+'_truth'] for r in rows],[r[task+'_pred'] for r in rows],average='macro'))
        assert abs(macro-result['validation_macro_f1'][task])<1e-12
    assert sha(folder/'validation_predictions.csv')==result['predictions_sha256']
    worker=Path(__file__).parent/'kaggle_micro_e13_pilot/worker.py'
    assert sha(worker)==result['source_sha256']
    minimum=min(metrics.values()); baseline=control['validation_micro_f1']
    rule=control['decision_rule']
    practical_go=(minimum>=.70 or (minimum>=min(baseline.values())+rule['minimum_gain_required'] and all(metrics[t]>=baseline[t]-rule['maximum_per_task_drop'] for t in e12.TASKS)))
    record={'status':'verified','validation_micro_f1':metrics,'control_micro_f1':baseline,
            'minimum_gain':minimum-min(baseline.values()),'practical_pilot_gate':practical_go,
            'eligible_as_oof':False,'target_740_oof_proven':False,
            'decision':'full evaluation may proceed' if practical_go else 'no expansion under frozen pilot gate',
            'limitation':'validation selected across epochs; pilot gate does not prove generalization'}
    e12.write_json(folder/'verification.json',record)
    return record


if __name__=='__main__':
    print(json.dumps({'E12':verify_e12(),'E13':verify_e13()},indent=2))
