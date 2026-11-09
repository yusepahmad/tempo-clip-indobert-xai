"""Verify each E14 outer fold and aggregate exactly 740 OOF predictions."""
import csv
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score

import build

TASKS=('task1_issue','task2_domain_sumber','task3_primary_entity_type')


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text())
def write(path,value):path.write_text(json.dumps(value,indent=2)+'\n')


def verify_fold(fold):
    folder=build.OUT/f'fold{fold}'
    result=read(folder/'result.json')
    protocol=read(build.OUT/'frozen_protocol.json')
    manifest=read(build.HERE/'build_manifest.json')
    assert result['status']=='complete' and not result['smoke'] and result['fold']==fold
    assert result['protocol_sha256']==sha(build.OUT/'frozen_protocol.json')
    assert result['source_sha256']==manifest['worker_sha256']==sha(build.HERE/'worker.py')
    assert re.fullmatch('[0-9a-f]{64}',result['initial_adapter_sha256'])
    assert re.fullmatch('[0-9a-f]{64}',result['adapter_sha256'])
    assert result['data_sha256']==protocol['dataset_sha256']
    assert result['predictions_sha256']==sha(folder/'predictions.csv')
    assert result['split_sha256']==sha(folder/'split.json')
    assert result['input_audit_sha256']==sha(folder/'input_audit.jsonl')
    split=read(folder/'split.json')
    inner,validation,train,test=map(set,(split['inner_train_ids'],split['inner_validation_ids'],split['outer_train_ids'],split['outer_test_ids']))
    assert (len(inner),len(validation),len(train),len(test))==(473,119,592,148)
    assert not inner&validation and inner|validation==train and not train&test
    assert train|test==set(protocol['fold_mapping'])
    assert test=={k for k,v in protocol['fold_mapping'].items() if v==fold}
    history=result['history']
    assert [r['epoch'] for r in history]==protocol['inner_epoch_candidates']
    for record in history:
        values=list(record['validation_micro_f1'].values())
        assert abs(record['minimum']-min(values))<1e-12
        assert abs(record['mean']-float(np.mean(values)))<1e-12
    chosen=max(history,key=lambda r:(r['minimum'],r['mean']))
    assert result['selected_epoch']==chosen['epoch']
    assert [r['epoch'] for r in result['refit_history']]==list(range(1,chosen['epoch']+1))
    assert result['outer_train_samples']==592 and result['samples']==148
    assert result['reused_pilot_inner_history']==(fold==1)
    data=pd.read_csv(build.APP/'03_data/DATASET_740_TASK2_DOMAIN.csv').set_index('sample_id')
    predictions=pd.read_csv(folder/'predictions.csv')
    assert len(predictions)==predictions.sample_id.nunique()==148
    assert set(predictions.sample_id)==test and set(predictions.fold)=={fold}
    for task in TASKS:
        truth=data.loc[predictions.sample_id,task].to_numpy()
        assert predictions[task+'_truth'].tolist()==truth.tolist()
        classes=result['classes'][task]
        probs=predictions[[task+'_p_'+label for label in classes]].to_numpy()
        assert np.isfinite(probs).all() and (probs>=0).all() and np.allclose(probs.sum(1),1.0,atol=1e-5)
        assert predictions[task+'_pred'].tolist()==np.asarray(classes)[probs.argmax(1)].tolist()
        score=float(f1_score(truth,predictions[task+'_pred'],average='micro'))
        assert abs(score-accuracy_score(truth,predictions[task+'_pred']))<1e-12
        assert abs(score-result['micro_f1'][task])<1e-12
    with (folder/'input_audit.jsonl').open() as handle:
        audits=[json.loads(line) for line in handle]
    assert len(audits)==2220
    assert {(r['sample_id'],r['task']) for r in audits}=={(sample_id,t) for sample_id in data.index for t in TASKS}
    record={'status':'verified','fold':fold,'samples':148,'selected_epoch':chosen['epoch'],
            'micro_f1':result['micro_f1'],'protocol_sha256':result['protocol_sha256'],
            'source_sha256':result['source_sha256'],
            'checks':['all 148 outer IDs','dataset labels','inner/test disjoint',
                      'inner epoch selection','exact refit epochs','probability argmax',
                      'micro equals accuracy','protocol/source/data/predictions/audit hashes'],
            'note':'adapter hash recorded remotely; large checkpoint not downloaded by default'}
    write(folder/'verification.json',record)
    files=sorted(p for p in folder.iterdir() if p.is_file() and p.name!='manifest_sha256.json')
    write(folder/'manifest_sha256.json',{'files':{p.name:sha(p) for p in files}})
    return record


def collect_fold(fold):
    folder=build.OUT/f'fold{fold}'
    folder.mkdir(exist_ok=True)
    if not (folder/'result.json').exists():
        raw=folder/'raw_kaggle'
        raw.mkdir(exist_ok=True)
        pattern=f'^e14_fold{fold}/(result\\.json|predictions\\.csv|split\\.json|input_audit\\.jsonl)$'
        subprocess.run(['kaggle','kernels','output',f'research-account/tempo-micro-e14-joint-qlora-fold{fold}',
                        '-p',str(raw),'--force','--file-pattern',pattern],check=True,timeout=240)
        source=raw/f'e14_fold{fold}'
        for path in source.iterdir():
            if path.is_file():shutil.copyfile(path,folder/path.name)
    return verify_fold(fold)


def aggregate():
    records=[verify_fold(f) for f in range(1,6)]
    frames=[pd.read_csv(build.OUT/f'fold{f}/predictions.csv') for f in range(1,6)]
    all_rows=pd.concat(frames,ignore_index=True)
    data=pd.read_csv(build.APP/'03_data/DATASET_740_TASK2_DOMAIN.csv')
    assert len(all_rows)==all_rows.sample_id.nunique()==740
    all_rows=all_rows.set_index('sample_id').loc[data.sample_id].reset_index()
    all_rows.to_csv(build.OUT/'predictions.csv',index=False)
    micro={t:float(f1_score(all_rows[t+'_truth'],all_rows[t+'_pred'],average='micro')) for t in TASKS}
    macro={t:float(f1_score(all_rows[t+'_truth'],all_rows[t+'_pred'],average='macro')) for t in TASKS}
    result={'schema':'tempo-e14-oof-v1','status':'complete','samples':740,'outer_folds':5,
            'model_contract':'one shared Qwen3-VL LoRA adapter per outer fold; identical joint training/selection/refit protocol',
            'micro_f1':micro,'macro_f1_diagnostic':macro,'minimum_micro_f1':min(micro.values()),
            'all_tasks_at_least_0_70':min(micro.values())>=.70,
            'protocol_sha256':sha(build.OUT/'frozen_protocol.json'),
            'source_sha256':sha(build.HERE/'worker.py'),'predictions_sha256':sha(build.OUT/'predictions.csv'),
            'fold_details':records,'limitation':'internal repeated-corpus CV; not independent acceptance data'}
    write(build.OUT/'result.json',result)
    write(build.OUT/'metrics.json',{k:result[k] for k in ('micro_f1','macro_f1_diagnostic','minimum_micro_f1','all_tasks_at_least_0_70')})
    (build.OUT/'decision.md').write_text(f'# MICRO-E14 740 OOF\n\nMicro-F1: {micro}.\nMinimum: {min(micro.values()):.6f}.\nGate each task >=0.70: {result["all_tasks_at_least_0_70"]}.\n\nInternal CV on repeatedly used corpus; independent generalization not established.\n')
    write(build.OUT/'verification.json',{'status':'verified','samples':740,'unique_ids':740,'outer_folds':5,
                                        'fold_checks':[r['status'] for r in records]})
    write(build.OUT/'manifest_sha256.json',{'files':{p.name:sha(p) for p in sorted(build.OUT.iterdir()) if p.is_file() and p.name not in ('manifest_sha256.json','scheduler_state.json','scheduler.log','scheduler.lock') and p.suffix not in ('.tmp','.lock')}})
    return result


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--fold',type=int,choices=range(1,6))
    args=parser.parse_args()
    print(json.dumps(collect_fold(args.fold) if args.fold else aggregate(),indent=2))
