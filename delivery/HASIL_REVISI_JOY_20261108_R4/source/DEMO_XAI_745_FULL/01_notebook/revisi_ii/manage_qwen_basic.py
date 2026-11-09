"""Paired basic-input QLoRA refits with the rich arm's inner-chosen epochs.

This isolates the input change conditional on the historically selected rich
recipe. It does not claim independent basic-input hyperparameter optimization.
"""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
from datetime import datetime,timezone
from evaluate import sha,write_json

HERE=Path(__file__).resolve().parent;APP=HERE.parents[1]
ORIGIN=HERE.parent/'next_research_20261017/kaggle_micro_e14'
OUT=APP/'04_hasil_eksperimen/revisi_ii/qwen_basic_jobs'
REF='research-account/tempo-revisi-ii-qwen-basic-'


def once(s,a,b):
    assert s.count(a)==1,a[:100]
    return s.replace(a,b)


def derive():
    s=(ORIGIN/'worker.py').read_text()
    s=once(s,'OUT = Path(f"/kaggle/working/e14_fold{FOLD}")','OUT = Path(f"/kaggle/working/rii_qwen_basic_fold{FOLD}")')
    start=s.index('    def aligned(name):');end=s.index('    classes = ',start)
    s=s[:start]+s[end:]
    start=s.index('        common = (');end=s.index('        cached[index] = {}',start)
    s=s[:start]+'''        common = (
            "Analisis sampul majalah Tempo tanpa memakai label anotasi. "
            f"Judul: {row.headline_verified}. Teks pendukung: {row.supporting_text_verified}. "
        )
'''+s[end:]
    s=once(s,'    assert torch.cuda.is_available()','''    if SMOKE:
        inner = inner[:8]
        validation = validation[:4]
        train = inner.copy()
        test = test[:4]
    assert torch.cuda.is_available()''')
    s=once(s,'    reused_history = prepare_reuse(frame, inner, validation, train, test, audits, model)','''    reused_history = None
    (OUT / "split.json").write_text(json.dumps(dict(train=train.tolist(), test=test.tolist(), inner=inner.tolist(), validation=validation.tolist()), indent=2))''')
    s=once(s,'    initial_state = capture_adapter(model)','''    if FOLD == 1 and not SMOKE:
        matches = [p for p in Path('/kaggle/input').rglob('initial_adapter_state.pt') if p.parent.name=='e13_inner_pilot']
        assert len(matches)==1
        restore_adapter(model, torch.load(matches[0], map_location='cpu', weights_only=True))
    initial_state = capture_adapter(model)
    torch.save(initial_state, OUT / "initial_adapter_state.pt")''')
    start=s.index('    seed_all(42 + FOLD)\n    optimizer = ')
    end=s.index('    # Refit from the exact initial adapter',start)
    s=s[:start]+'''    # Fixed from rich-arm inner selection, never from test performance.
    selected_epoch = 1 if SMOKE else [3,1,3,2,3][FOLD-1]
    criterion = nn.CrossEntropyLoss()
    history = []
'''+s[end:]
    s=once(s,'    del optimizer, scaler\n','')
    s=once(s,'        selected = output.logits[:, -1, :].index_select(-1, code_ids[task]).float()',
        '''        if time.monotonic()-run_started > (1800 if SMOKE else 32400):
            raise RuntimeError("Basic QLoRA wall-time guard exceeded")
        selected = output.logits[:, -1, :].index_select(-1, code_ids[task]).float()''')
    s=once(s,'        "minimum_micro_f1": min(micro.values()), "all_tasks_at_least_0_70": min(micro.values()) >= 0.70,',
        '''        "macro_f1": {task: float(f1_score(truth[task][test], predictions[task], labels=range(len(classes[task])), average="macro", zero_division=0)) for task in TASKS},
        "primary_metric": "macro_f1", "input_scope": "image384+headline+supporting only; no E01 features",
        "epoch_source": "fixed from corresponding rich E14 inner selection; no basic retuning",''')
    s=s.replace('"schema": "tempo-e14-fold-v1"','"schema": "revisi-ii-qwen-basic-paired-v1"')
    # No historical CV helper is called. Drop it to keep the dependency graph clear.
    start=s.index('\ndef prepare_reuse(')
    s=s[:start]+'\nif __name__ == "__main__":\n    main()\n'
    compile(s,'qwen_basic_worker.py','exec')
    p=HERE/'qwen_basic_worker.py'
    if p.exists():assert p.read_text()==s
    else:p.write_text(s)
    return p


def build(mode):
    worker=derive();kernel=OUT/mode/'kernel';kernel.mkdir(parents=True,exist_ok=True)
    protocol=dict(schema='revisi-ii-qwen-basic-protocol-v1',model='Qwen/Qwen3-VL-8B-Instruct',revision='0c351dd01ed87e9c1b53cbc748cba10e6187ff3b',
        data_sha256='cba20f8250bcb59481ed2d3d7d5d42fb8242c96a7ba2d11a2cd02ad80862961a',
        input_fields=['image384','headline_verified','supporting_text_verified'],excluded=['deskripsi','sumber_visual','alasan','gold in prompt'],
        fixed_epochs=[3,1,3,2,3],epoch_source='historical rich inner-validation choices, conditional paired-input comparison, no outer-test selection',
        primary_metric='macro_f1',wall_seconds_limit=1800 if mode=='smoke' else 32400,
        source_sha256=sha(worker),derived_from_sha256=sha(ORIGIN/'worker.py'),smoke=mode=='smoke')
    launch='import os,sys,subprocess,time\nfrom pathlib import Path\n'
    launch+=next(l for l in (ORIGIN/'fold5/launch.py').read_text().splitlines() if "'-m','pip'" in l)+'\n'
    launch+=f"os.environ['E07_SMOKE']={'1' if mode=='smoke' else '0'!r}\n"
    launch+=f"Path('/kaggle/working/protocol.json').write_text({json.dumps(protocol,indent=2)!r})\n"
    launch+=f"Path('/kaggle/working/qwen_basic_worker.py').write_text({worker.read_text()!r})\n"
    launch+="started=time.monotonic()\n"
    launch+=f"for fold in {([1] if mode=='smoke' else [1,2,3,4,5])!r}:\n"
    launch+="    os.environ['E07_FOLD']=str(fold)\n    remaining=int(32400-(time.monotonic()-started))\n    assert remaining>0\n    subprocess.run([sys.executable,'-u','/kaggle/working/qwen_basic_worker.py'],check=True,timeout=remaining)\n"
    launch+="Path('/kaggle/working/COMPLETED.json').write_text('{\"status\":\"complete\"}')\n"
    compile(launch,'launch.py','exec');(kernel/'launch.py').write_text(launch)
    meta=json.loads((ORIGIN/'fold5/kernel-metadata.json').read_text())
    meta.update(id=REF+mode,title='Tempo Revisi II Qwen Basic '+mode.title(),is_private=True,
                kernel_sources=['research-account/tempo-micro-e13-joint-qlora-inner-pilot'] if mode=='full' else [])
    write_json(kernel/'kernel-metadata.json',meta);write_json(OUT/mode/'protocol.json',protocol)
    return kernel


def status(mode):
    r=subprocess.run(['kaggle','kernels','status',REF+mode],capture_output=True,text=True,timeout=90)
    match=re.search(r'KernelWorkerStatus\.([A-Z_]+)',r.stdout)
    if r.returncode or not match:raise RuntimeError((r.stderr or r.stdout)[:1000])
    value=dict(kernel=REF+mode,status=match[1],observed_at=datetime.now(timezone.utc).isoformat());write_json(OUT/mode/'status.json',value);print(json.dumps(value));return match[1]


def submit(mode):
    ledger=OUT/mode/'submission.json'
    prior=[]
    if ledger.exists():
        old=json.loads(ledger.read_text())
        failed_retry = old['state']=='failed_smoke_archived' and mode=='smoke'
        if old['state']!='rejected_capacity' and not failed_retry:raise RuntimeError('Submission record exists; do not duplicate push')
        check=subprocess.run(['kaggle','kernels','status',REF+mode],capture_output=True,text=True,timeout=90)
        observed=check.stdout+'\n'+check.stderr
        absent=any(s in observed.lower() for s in ['404','not found','notfound'])
        cancelled='KernelWorkerStatus.CANCEL_ACKNOWLEDGED' in observed
        failed = failed_retry and 'KernelWorkerStatus.ERROR' in observed
        if not absent and not cancelled and not failed:
            raise RuntimeError('Cannot prove rejected job was not created; inspect status before retry')
        prior=old.get('attempts',[])+[{'state':old['state'],'output':old.get('output',''),'negative_status_observation':observed}]
    if mode=='full':
        smoke=json.loads((OUT/'smoke/verification.json').read_text());assert smoke['status']=='verified' and smoke['source_sha256']==sha(derive())
    kernel=build(mode);write_json(ledger,dict(state='submission_intent',kernel=REF+mode,version=1,attempts=prior))
    r=subprocess.run(['kaggle','kernels','push','-p',str(kernel)],capture_output=True,text=True,timeout=120)
    match=re.search(r'Kernel version (\d+) successfully pushed',r.stdout)
    success=r.returncode==0 and match is not None
    capacity='Maximum batch GPU session count' in r.stdout+r.stderr
    write_json(ledger,dict(state='submitted' if success else 'rejected_capacity' if capacity else 'push_ambiguous',
                          kernel=REF+mode,version=int(match[1]) if match else None,output=r.stdout,stderr=r.stderr,attempts=prior))
    if not success:raise RuntimeError((r.stderr or r.stdout)[:1500])
    print(r.stdout)


def collect(mode):
    if status(mode)!='COMPLETE':raise RuntimeError('Basic QLoRA not complete')
    raw=OUT/mode/'raw';raw.mkdir(parents=True,exist_ok=True)
    r=subprocess.run(['kaggle','kernels','output',REF+mode,'-p',str(raw),'-q','--file-pattern',r'.*\.(json|jsonl|csv)$'],capture_output=True,text=True,timeout=300)
    if r.returncode:raise RuntimeError((r.stderr or r.stdout)[:1000])
    assert json.loads((raw/'COMPLETED.json').read_text())['status']=='complete'
    remote=raw/'protocol.json';assert json.loads(remote.read_text())==json.loads((OUT/mode/'protocol.json').read_text())
    import pandas as pd
    frames=[]
    for fold in ([1] if mode=='smoke' else range(1,6)):
        folder=raw/f'rii_qwen_basic_fold{fold}';result=json.loads((folder/'result.json').read_text())
        assert result['status']=='complete' and result['source_sha256']==sha(derive())
        assert result['protocol_sha256']==sha(remote) and result['predictions_sha256']==sha(folder/'predictions.csv')
        split=json.loads((folder/'split.json').read_text());assert not set(split['train'])&set(split['test'])
        assert result['selected_epoch']==(1 if mode=='smoke' else [3,1,3,2,3][fold-1])
        frames.append(pd.read_csv(folder/'predictions.csv'))
    if mode=='full':
        combined=pd.concat(frames,ignore_index=True);assert len(combined)==combined.sample_id.nunique()==740
        # Do not publish an aggregate just because there are 740 rows.
        import numpy as np
        from evaluate import TASKS,validate_predictions
        reference=pd.read_csv(APP/'03_data/DATASET_740_TASK2_DOMAIN.csv').fillna('')
        folds=pd.read_csv(APP/'04_hasil_eksperimen/e42_tail_grid/oof.csv').set_index('sample_id')['fold']
        validate_predictions(combined,reference,folds)
        assert combined.groupby('fold').size().to_dict()=={f:148 for f in range(1,6)}
        for fold in range(1,6):
            folder=raw/f'rii_qwen_basic_fold{fold}'
            split=json.loads((folder/'split.json').read_text());r=json.loads((folder/'result.json').read_text())
            assert r['fold']==fold and r['smoke'] is False and r['samples']==148 and r['outer_train_samples']==592
            assert r['split_sha256']==sha(folder/'split.json') and r['data_sha256']==sha(APP/'03_data/DATASET_740_TASK2_DOMAIN.csv')
            assert r['input_audit_sha256']==sha(folder/'input_audit.jsonl')
            audit=[json.loads(line) for line in (folder/'input_audit.jsonl').read_text().splitlines() if line.strip()]
            assert len(audit)==2220 and {(a['sample_id'],a['task']) for a in audit}=={(sid,t) for sid in reference.sample_id for t in TASKS}
            assert all(0<a['tokens']<=2048 and len(a['prompt_sha256'])==64 for a in audit)
            train=set(split['train']);test=set(split['test'])
            assert len(train)==592 and len(test)==148 and train|test==set(range(740))
            expected=set(np.flatnonzero(reference.sample_id.map(folds).to_numpy()==fold))
            assert test==expected and set(combined.loc[combined.fold.eq(fold),'index'])==test
        for task in TASKS:
            labels=sorted(reference[task].unique());columns=[f'{task}_p_{label}' for label in labels]
            probs=combined[columns].to_numpy(float)
            assert np.isfinite(probs).all() and (probs>=0).all() and (probs<=1).all()
            assert np.allclose(probs.sum(1),1,atol=1e-5)
            assert np.array_equal(np.asarray(labels)[probs.argmax(1)],combined[task+'_pred'].to_numpy())
        dest=APP/'04_hasil_eksperimen/revisi_ii/experiments/RII_QWEN_QLORA_BASIC';dest.mkdir(parents=True,exist_ok=True)
        target=dest/'predictions.csv'
        if target.exists():assert pd.read_csv(target).equals(combined)
        else:combined.to_csv(target,index=False)
        write_json(dest/'result.json',dict(status='complete',samples=740,predictions_sha256=sha(target),protocol_sha256=sha(remote),
                   source_sha256=sha(derive()),folds=[json.loads((raw/f'rii_qwen_basic_fold{f}/result.json').read_text()) for f in range(1,6)]))
    write_json(OUT/mode/'verification.json',dict(status='verified',source_sha256=sha(derive()),protocol_sha256=sha(remote),
        samples=4 if mode=='smoke' else 740,mode=mode))
    print('QWEN BASIC VERIFIED',mode)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['build','submit','status','collect']);ap.add_argument('mode',choices=['smoke','full']);a=ap.parse_args();globals()[a.action](a.mode)
