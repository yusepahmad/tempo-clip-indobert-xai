"""Submit once, inspect and verify CI-D01. No ambiguous automatic repush."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import StratifiedKFold

import build
from protocol_utils import TASKS, sha, write

LEDGER=build.OUT/'job_state.json'


def load():
    return json.loads(LEDGER.read_text()) if LEDGER.exists() else {}


def save(state):
    state['updated_at']=datetime.now(timezone.utc).isoformat()
    tmp=LEDGER.with_suffix('.tmp');write(tmp,state);tmp.replace(LEDGER)


def assert_build():
    manifest=json.loads((build.HERE/'build_manifest.json').read_text())
    for name,h in manifest['payload'].items():assert sha(build.HERE/name)==h,name
    for name,h in manifest['kernel_files'].items():assert sha(build.HERE/name)==h,name


def ref(mode):return f'research-account/tempo-ci-d01-clip-indobert-dup2-{mode}'


def status(mode):
    run=subprocess.run(['kaggle','kernels','status',ref(mode)],capture_output=True,text=True,timeout=90)
    match=re.search(r'KernelWorkerStatus\.([A-Z_]+)',run.stdout)
    if run.returncode or not match:raise RuntimeError((run.stderr or run.stdout)[:1000])
    state=load();state.setdefault(mode,{}).update(kernel=ref(mode),status=match[1],observed_at=datetime.now(timezone.utc).isoformat())
    save(state);print(json.dumps(state[mode]));return match[1]


def submit(mode):
    assert_build()
    state=load()
    if mode in state:raise RuntimeError('Job handle/intent already recorded; inspect status, never blindly repush')
    if mode=='full':
        verify_smoke(build.OUT/'smoke/raw/ci_d01_smoke')
    state[mode]=dict(kernel=ref(mode),status='SUBMITTING',intent_at=datetime.now(timezone.utc).isoformat())
    save(state)
    try:
        run=subprocess.run(['kaggle','kernels','push','-p',str(build.HERE/mode),'--accelerator','NvidiaTeslaT4'],capture_output=True,text=True,timeout=180)
        state[mode]['submission_stdout']=run.stdout[-3000:]
        state[mode]['submission_stderr']=run.stderr[-1000:]
        match=re.search(r'Kernel version (\d+) successfully pushed',run.stdout)
        if run.returncode or not match:raise RuntimeError('Submission unclear; inspect recorded response before any retry')
        state[mode].update(status='SUBMITTED',version=int(match[1]));save(state)
        print(run.stdout)
    except Exception:
        state[mode]['status']='SUBMISSION_AMBIGUOUS';save(state);raise
    status(mode)


def verify_smoke(folder):
    folder=Path(folder)
    report=json.loads((folder/'smoke.json').read_text())
    assert_build()
    assert report['status']=='passed' and report['schema']=='ci-d01-smoke-v1'
    assert report['protocol_sha256']==sha(build.HERE/'frozen_protocol.json')
    assert report['source_sha256']==sha(build.HERE/'worker.py')
    assert re.fullmatch('[0-9a-f]{64}',report['initial_state_sha256'])
    for factor in (1,2):
        arm=report['arms'][f'{factor}x']
        assert arm['cpu_save_reload_identical'] is True
        assert len(arm['changes'])==6 and all(np.isfinite(v) and v>0 for v in arm['changes'].values())
        assert arm['training']['exposures']==40*factor and arm['training']['unique_train_samples']==40
        assert arm['training']['batches']==(2 if factor==1 else 3)
        split=arm['split']
        assert len(split['train_ids'])==len(set(split['train_ids']))==40
        assert not set(split['train_ids'])&set(split['test_ids'])
        assert split['factor']==factor and split['train_exposures_per_epoch']==40*factor
        assert set(split['multiplicity'])==set(split['train_ids']) and set(split['multiplicity'].values())=={factor}
    record=dict(status='verified',kind='GPU gradients + exact duplication + CPU checkpoint roundtrip; NOT benchmark',
                verified_at=datetime.now(timezone.utc).isoformat(),smoke_sha256=sha(folder/'smoke.json'))
    write(build.OUT/'smoke/verification.json',record)
    return record


def verify_full(folder):
    assert_build()
    folder=Path(folder)
    result=json.loads((folder/'result.json').read_text())
    protocol=json.loads((build.HERE/'frozen_protocol.json').read_text())
    data=pd.read_csv(build.APP/'03_data/DATASET_740_TASK2_DOMAIN.csv').fillna('')
    ids=data.sample_id.tolist();folds=np.array([protocol['fold_mapping'][i] for i in ids])
    assert result['status']=='complete' and result['samples']==result['unique_original_samples']==740
    assert result['protocol_sha256']==sha(build.HERE/'frozen_protocol.json')
    assert result['worker_sha256']==sha(build.HERE/'worker.py')
    assert result['canonical_precision']=='CPU FP32 checkpoint reload'
    metrics={}
    for factor in (1,2):
        path=folder/f'oof_{factor}x.csv'
        assert sha(path)==result['files'][path.name]
        pred=pd.read_csv(path)
        assert len(pred)==pred.sample_id.nunique()==740 and pred.sample_id.tolist()==ids and pred.fold.tolist()==folds.tolist()
        metrics[str(factor)]={}
        for task in TASKS:
            classes=sorted(data[task].unique());truth=data[task].tolist();labels=pred[task+'_pred'].tolist()
            assert result['classes'][task]==classes and pred[task+'_truth'].tolist()==truth
            prob=pred[[task+'_p_'+c for c in classes]].to_numpy()
            assert np.isfinite(prob).all() and (prob>=0).all() and np.allclose(prob.sum(1),1,atol=1e-5)
            assert labels==np.asarray(classes)[prob.argmax(1)].tolist()
            values=dict(macro_f1=float(f1_score(truth,labels,labels=classes,average='macro',zero_division=0)),
                        micro_f1=float(f1_score(truth,labels,average='micro')),accuracy=float(accuracy_score(truth,labels)),
                        precision_macro=float(precision_score(truth,labels,labels=classes,average='macro',zero_division=0)),
                        recall_macro=float(recall_score(truth,labels,labels=classes,average='macro',zero_division=0)))
            for name,value in values.items():assert abs(value-result['metrics'][str(factor)][task][name])<1e-12
            metrics[str(factor)][task]=values
        assert result['all_tasks_macro_f1_at_least_0_70'][str(factor)]==all(metrics[str(factor)][t]['macro_f1']>=.7 for t in TASKS)
    def audit(split,train,valid,test,factor):
        assert split['train_ids']==[ids[i] for i in train]
        assert split['validation_ids']==[ids[i] for i in valid]
        assert split['test_ids']==[ids[i] for i in test]
        assert not set(split['train_ids'])&set(split['validation_ids'])
        assert not set(split['train_ids'])&set(split['test_ids'])
        assert split['unique_train_samples']==len(train) and split['train_exposures_per_epoch']==len(train)*factor
        assert split['factor']==factor and split['multiplicity']=={ids[i]:factor for i in train}
    for fold in range(1,6):
        record=json.loads((folder/f'fold{fold}.json').read_text())
        assert record['fold']==fold
        train=np.where(folds!=fold)[0];test=np.where(folds==fold)[0]
        inner=[(train[a],train[b]) for a,b in StratifiedKFold(2,shuffle=True,random_state=123).split(train,data.iloc[train][TASKS[1]])]
        for factor in (1,2):
            arm=record['arms'][str(factor)]
            audit(arm['split'],train,[],test,factor)
            assert len(arm['traces'])==2
            for trace,(a,b) in zip(arm['traces'],inner):
                audit(trace['split'],a,b,test,factor)
                assert len(trace['training'])==max(protocol['config']['epoch_candidates'])
                for history in trace['training']:
                    assert history['exposures']==len(a)*factor and history['unique_train_samples']==len(a)
                    assert history['batches']==int(np.ceil(len(a)*factor/protocol['config']['batch']))
                    assert history['optimizer_updates']+history['skipped_updates']==history['batches']
            scores={e:min(sum(trace['epochs'][str(e)][t] for trace in arm['traces'])/2 for t in TASKS) for e in protocol['config']['epoch_candidates']}
            chosen=max(protocol['config']['epoch_candidates'],key=lambda e:scores[e])
            assert chosen==arm['selected_epoch']
            for e,v in scores.items():assert abs(v-arm['epoch_scores'][str(e)])<1e-12
            assert [h['epoch'] for h in arm['training']]==list(range(1,chosen+1))
            for h in arm['training']:
                assert h['exposures']==592*factor and h['batches']==int(np.ceil(592*factor/32))
            assert re.fullmatch('[0-9a-f]{64}',arm['checkpoint_sha256'])
        assert record['arms']['1']['initial_state_sha256']==record['arms']['2']['initial_state_sha256']
        for j in (0,1):assert record['arms']['1']['traces'][j]['initial_state_sha256']==record['arms']['2']['traces'][j]['initial_state_sha256']
    for t in TASKS:
        for name in metrics['1'][t]:assert abs(metrics['2'][t][name]-metrics['1'][t][name]-result['deltas_2x_minus_1x'][t][name])<1e-12
    verification=dict(status='verified',verified_at=datetime.now(timezone.utc).isoformat(),metrics=metrics,
           checks=['740 unique OOF IDs per arm','ground-truth/probabilities/metrics','all 5 nested splits','train-only multiplicity',
                   'paired identical initialization','inner-only selection','epoch/exposure/update counts','source/protocol hashes'],
           checkpoint_note='CPU checkpoint reload executed by frozen Kaggle worker; large checkpoint hashes recorded remotely, not downloaded/replayed locally',
           result_sha256=sha(folder/'result.json'))
    write(build.OUT/'full/verification.json',verification)
    return verification


def collect(mode):
    if status(mode)!='COMPLETE':print('Not complete; nothing installed or resubmitted.');return
    raw=build.OUT/mode/'raw';raw.mkdir(parents=True,exist_ok=True)
    pattern=(r'^ci_d01_smoke/(smoke\.json|runtime\.json)$' if mode=='smoke' else
             r'^ci_d01_dup2/(result\.json|runtime\.json|fold[1-5]\.json|oof_[12]x\.csv)$')
    subprocess.run(['kaggle','kernels','output',ref(mode),'-p',str(raw),'--force','--file-pattern',pattern],check=True,timeout=240)
    folder=raw/('ci_d01_smoke' if mode=='smoke' else 'ci_d01_dup2')
    report=verify_smoke(folder) if mode=='smoke' else verify_full(folder)
    if mode=='full':
        result=json.loads((folder/'result.json').read_text())
        labels=('Isu utama','Domain sumber metafora','Sasaran kritik')
        lines=['# CI-D01 — hasil duplikasi training CLIP–IndoBERT 2×','',
               'Status: VERIFIED; dua arm, masing-masing740 prediksi OOF CPU FP32.','',
               '| Task | Macro-F1 1× | Macro-F1 2× | Delta pp | Micro-F1 1× | Micro-F1 2× |',
               '|---|---:|---:|---:|---:|---:|']
        for t,label in zip(TASKS,labels):
            a,b=result['metrics']['1'][t],result['metrics']['2'][t]
            lines.append(f"| {label} | {a['macro_f1']:.6f} | {b['macro_f1']:.6f} | {100*(b['macro_f1']-a['macro_f1']):+.2f} | {a['micro_f1']:.6f} | {b['micro_f1']:.6f} |")
        for factor in (1,2):
            minimum=min(result['metrics'][str(factor)][t]['macro_f1'] for t in TASKS)
            lines.extend(['',f"Minimum Macro-F1 arm{factor}×: **{minimum:.6f}**. Semua task≥0,70: **{result['all_tasks_macro_f1_at_least_0_70'][str(factor)]}**."])
        lines.extend(['','Salinan persis, bukan1.480 sampel independen. Split berdasarkan ID sebelum duplikasi.',
                      'Kontrol berpasangan dengan resep tetap; tidak optimizer-step matched. Evaluasi internal pada korpus berulang, bukan test eksternal.',
                      'Canonical CPU checkpoint reload dijalankan worker Kaggle; checkpoint besar belum direplay lokal.',
                      'Tidak mengubah model web atau menganggap checkpoint CV sebagai model produksi.',
                      '',f"Durasi worker tercatat: {result['seconds']:.3f}detik. RAM/VRAM/utilisasi: Not Recorded.",
                      f"Result SHA256: `{sha(folder/'result.json')}`.",
                      f"Protokol SHA256: `{result['protocol_sha256']}`."])
        (build.OUT/'CI_D01_REPORT.md').write_text('\n'.join(lines)+'\n')
    state=load();state[mode]['verification']='VERIFIED';save(state)
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['submit','status','collect'])
    parser.add_argument('mode',choices=['smoke','full'])
    args=parser.parse_args()
    {'submit':submit,'status':status,'collect':collect}[args.action](args.mode)
