"""Schedule unsubmitted E12 folds conservatively; never restart uncertain jobs."""
import argparse
import ast
from datetime import datetime,timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time

ROOT=Path(__file__).resolve().parents[1]
LEARN=ROOT.parent
CLI=LEARN/'.kaggle/cli/bin/kaggle'
os.environ['KAGGLE_CONFIG_DIR']=str(LEARN/'.kaggle')
from kaggle.api.kaggle_api_extended import KaggleApi
from kagglesdk.kernels.types.kernels_api_service import ApiGetAcceleratorQuotaStatisticsRequest
OUT=ROOT/'04_hasil_eksperimen/e12_monitor'
WORKER_HASH='64f6a1bd2a3701c303335677e02920f1c6fcc35652e7b1c4f7e6e41950dc76d1'
LIMIT=28800
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
slug=lambda k:f'yusepmuhamadzazuli/tempo-e12-qlora-fold{k}'

def cli(*args,timeout=120):
    return subprocess.run([str(CLI),*args],capture_output=True,text=True,timeout=timeout)

def status(k):
    result=cli('kernels','status',slug(k))
    if result.returncode:raise RuntimeError(f'status fold{k} unavailable: exit{result.returncode}')
    match=re.search(r'KernelWorkerStatus\.([A-Z_]+)',result.stdout)
    if not match:raise RuntimeError(f'unknown status format fold{k}')
    return match.group(1)

def quota():
    api=KaggleApi();api.authenticate()
    with api.build_kaggle_client() as client:
        q=client.kernels.kernels_api_client.get_accelerator_quota_statistics(
            ApiGetAcceleratorQuotaStatisticsRequest()).gpu_quota
        used,reserved,allowed=[v.total_seconds() for v in (q.time_used,q.time_reserved,q.total_time_allowed)]
    assert min(used,reserved,allowed)>=0
    return {'used_seconds':used,'reserved_seconds':reserved,'allowed_seconds':allowed,
            'available_seconds':allowed-used-reserved}

def launcher(k):
    folder=ROOT/f'01_notebook/kaggle_e12/fold{k}'
    assert sha(ROOT/'01_notebook/kaggle_e12/worker.py')==WORKER_HASH
    source=(folder/'launch.py').read_text();tree=ast.parse(source)
    flags={};timeouts=[];embedded=None
    for node in tree.body:
        if isinstance(node,ast.Assign) and isinstance(node.targets[0],ast.Subscript):
            flags[ast.literal_eval(node.targets[0].slice)]=ast.literal_eval(node.value)
    for node in ast.walk(tree):
        if isinstance(node,ast.Call):
            for keyword in node.keywords:
                if keyword.arg=='timeout':timeouts.append(ast.literal_eval(keyword.value))
            if isinstance(node.func,ast.Attribute) and node.func.attr=='write_text':embedded=ast.literal_eval(node.args[0])
    assert flags['E12_SMOKE']=='0' and flags['E12_FOLD']==str(k) and timeouts==[900,27600]
    assert hashlib.sha256(embedded.encode()).hexdigest()==WORKER_HASH
    meta=json.loads((folder/'kernel-metadata.json').read_text())
    assert meta['id']==slug(k) and meta['is_private'] and meta['enable_gpu']
    return folder,source

def save(state):
    state['updated_at']=datetime.now(timezone.utc).isoformat()
    temp=OUT/'state.tmp';temp.write_text(json.dumps(state,indent=2)+'\n');temp.replace(OUT/'state.json')

def event(kind,**fields):
    row={'at':datetime.now(timezone.utc).isoformat(),'event':kind,**fields}
    with (OUT/'events.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
    print(json.dumps(row),flush=True)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true')
    ap.add_argument('--hold-new-submissions',action='store_true');args=ap.parse_args()
    for k in range(1,6):launcher(k)
    if args.check:
        print(json.dumps({'launchers':'verified','fold1':status(1),'fold2':status(2),'quota':quota()},indent=2));return
    OUT.mkdir(exist_ok=True)
    lock=(OUT/'monitor.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    if (OUT/'state.json').exists():state=json.loads((OUT/'state.json').read_text())
    else:
        state={'phase':'watching','folds':{str(k):{'phase':'submitted' if k<=2 else 'pending'} for k in range(1,6)}}
        save(state)
    if state['phase']!='watching':raise RuntimeError('Monitor requires root audit before resuming this state')
    state['hold_new_submissions']=args.hold_new_submissions
    state['monitor_pid']=os.getpid();save(state)
    event('started',pid=os.getpid())
    while True:
        try:
            active=[]
            for k in range(1,6):
                item=state['folds'][str(k)]
                if item['phase']=='submitting':
                    state['phase']='needs_root_audit';save(state)
                    raise RuntimeError('uncertain submission requires root audit')
                if item['phase']!='submitted':continue
                value=status(k);item['status']=value
                if value in ('RUNNING','QUEUED'):active.append(k)
                elif value=='COMPLETE':
                    target=ROOT/f'04_hasil_eksperimen/e12_qlora/fold{k}'
                    result=cli('kernels','output',slug(k),'-p',str(target),
                               '--file-pattern',f'^e12_fold{k}/.*\\.(json|jsonl|csv)$')
                    if result.returncode:raise RuntimeError(f'download fold{k} failed')
                    for name in ('config.json','metrics.json','history.jsonl','input_audit.jsonl','oof.csv'):
                        if not (target/f'e12_fold{k}'/name).is_file():raise RuntimeError(f'fold{k} artifact {name} not published yet')
                    item['phase']='downloaded';event('downloaded',fold=k)
                else:
                    state['phase']='needs_root_audit';save(state)
                    event('unexpected_terminal_status',fold=k,status=value);return
            save(state)
            if all(item['phase']=='downloaded' for item in state['folds'].values()):
                result=subprocess.run([str(ROOT/'venv/bin/python'),str(ROOT/'01_notebook/kaggle_e12/aggregate.py')],
                                      capture_output=True,text=True,timeout=300)
                (OUT/'aggregate.log').write_text(result.stdout+result.stderr)
                state['phase']='aggregate_ready_for_root_audit' if result.returncode==0 else 'needs_root_audit'
                save(state);event('aggregated',exit_code=result.returncode);return
            pending=[k for k in range(3,6) if state['folds'][str(k)]['phase']=='pending']
            if pending and len(active)<2 and not args.hold_new_submissions:
                q=quota();state['quota']=q;save(state)
                # Reservations may already include live jobs; subtracting again is deliberately conservative.
                if q['available_seconds']-len(active)*LIMIT>=LIMIT:
                    k=pending[0];folder,source=launcher(k);item=state['folds'][str(k)]
                    (OUT/f'fold{k}_submitted.py').write_text(source)
                    item.update(phase='submitting',source_sha256=hashlib.sha256(source.encode()).hexdigest());save(state)
                    try:result=cli('kernels','push','-p',str(folder),'--accelerator','NvidiaTeslaT4','--timeout',str(LIMIT))
                    except Exception:
                        state['phase']='needs_root_audit';save(state);raise
                    (OUT/f'fold{k}_push.log').write_text(result.stdout+result.stderr)
                    if result.returncode!=0 or 'successfully pushed' not in result.stdout:
                        state['phase']='needs_root_audit';save(state);event('uncertain_submission',fold=k);return
                    item['phase']='submitted';save(state);event('submitted',fold=k,quota=q)
                else:event('waiting_for_quota',active=active,quota=q)
        except Exception as error:
            event('observation_error',error=str(error))
            if state['phase']!='watching':return
        time.sleep(45)

if __name__=='__main__':main()
