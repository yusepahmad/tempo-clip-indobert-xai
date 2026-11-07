"""Durable E14 job queue. Never repush a submitted job after a polling timeout."""
import argparse
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

import build
import results

LEDGER=build.OUT/'scheduler_state.json'
ACTIVE={'QUEUED','RUNNING'}


def event(message):
    print(datetime.now(timezone.utc).isoformat(),message,flush=True)


def save(state):
    state['updated_at']=datetime.now(timezone.utc).isoformat()
    temporary=LEDGER.with_suffix('.tmp')
    temporary.write_text(json.dumps(state,indent=2)+'\n')
    temporary.replace(LEDGER)


def status(ref):
    completed=subprocess.run(['kaggle','kernels','status',ref],capture_output=True,text=True,timeout=90)
    match=re.search(r'KernelWorkerStatus\.([A-Z_]+)',completed.stdout)
    if completed.returncode or not match:
        raise RuntimeError(f'Polling failed for existing job {ref}: {(completed.stderr or completed.stdout)[:500]}')
    return match[1]


def assert_build():
    manifest=results.read(build.HERE/'build_manifest.json')
    assert manifest['worker_sha256']==results.sha(build.HERE/'worker.py')
    assert manifest['protocol_sha256']==results.sha(build.OUT/'frozen_protocol.json')
    for fold in range(1,6):
        for name in ('launch.py','kernel-metadata.json'):
            relative=f'fold{fold}/{name}'
            assert results.sha(build.HERE/relative)==manifest['files'][relative],relative


def tick(state):
    assert_build()
    # Only submitted handles are polled. An API failure does not imply a job stopped.
    for fold in range(1,6):
        job=state['jobs'][str(fold)]
        if job['state'] in ('PENDING','VERIFIED','FAILED'):
            continue
        if job['state']=='SUBMITTING':
            raise RuntimeError('Uncertain submission detected. Reconcile exact kernel/version before any retry: '+job['kernel'])
        observed=status(job['kernel'])
        job['observed_status']=observed
        if observed=='COMPLETE':
            job['state']='COLLECTING';save(state)
            try:
                record=results.collect_fold(fold)
            except (subprocess.TimeoutExpired,subprocess.CalledProcessError) as error:
                event(f'fold{fold} collection transient failure; completed job retained: {error}')
                continue
            job['state']='VERIFIED';job['verification']=record
            event(f'fold{fold} VERIFIED {record["micro_f1"]}')
        elif observed not in ACTIVE:
            job['state']='FAILED'
            event(f'fold{fold} terminal {observed}; no automatic restart; stop launching more jobs for diagnosis')
        else:
            job['state']=observed
        save(state)
    if any(j['state']=='FAILED' for j in state['jobs'].values()):
        return 'needs_diagnosis'
    active=sum(j['state'] in ACTIVE|{'COLLECTING'} for j in state['jobs'].values())
    for fold in range(1,6):
        job=state['jobs'][str(fold)]
        if job['state']!='PENDING' or active>=2:
            continue
        job['state']='SUBMITTING';save(state)
        try:
            pushed=subprocess.run(['kaggle','kernels','push','-p',str(build.HERE/f'fold{fold}')],
                                  capture_output=True,text=True,timeout=120)
        except subprocess.TimeoutExpired:
            raise RuntimeError('Submission timed out; handle uncertain, will not repush: '+job['kernel'])
        response=pushed.stdout+'\n'+pushed.stderr
        match=re.search(r'Kernel version (\d+) successfully pushed',response)
        if not match:
            if 'Maximum batch GPU session count' in response:
                job['state']='PENDING';save(state)
                event('Kaggle session limit reached; defer submission until a slot is available')
                break
            job['submission_response']=response[:2000];save(state)
            raise RuntimeError('Uncertain/failed push. No automatic repush: '+response[:500])
        assert job['kernel'] in response,response
        job.update(state='QUEUED',version=int(match[1]),submitted_at=datetime.now(timezone.utc).isoformat())
        active+=1;save(state)
        event(f'fold{fold} submitted version {job["version"]}')
    if all(j['state']=='VERIFIED' for j in state['jobs'].values()):
        combined=results.aggregate()
        event('ALL_FOLDS_COMPLETE '+json.dumps(combined['micro_f1']))
        state['status']='complete';save(state)
        subprocess.run([sys.executable,str(build.HERE.parent/'finalize_micro_f1.py')],check=True)
        return 'complete'
    return 'waiting'


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--once',action='store_true')
    args=parser.parse_args()
    build.OUT.mkdir(exist_ok=True)
    with (build.OUT/'scheduler.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if LEDGER.exists():
            state=results.read(LEDGER)
        else:
            # A nonempty pre-existing remote E14 family must be reconciled instead
            # of creating a new version over an unknown active run.
            listed=subprocess.run(['kaggle','kernels','list','--mine','--search','Tempo Micro E14 Joint QLoRA','--page-size','100'],capture_output=True,text=True,timeout=90)
            assert listed.returncode==0,listed.stderr
            assert 'yusepmuhamadzazuli/tempo-micro-e14-joint-qlora-fold' not in listed.stdout,'Remote family exists without local ledger; reconcile first'
            state={'schema':'tempo-e14-scheduler-v1','status':'active',
                   'protocol_sha256':results.sha(build.OUT/'frozen_protocol.json'),
                   'jobs':{str(f):{'state':'PENDING','kernel':f'yusepmuhamadzazuli/tempo-micro-e14-joint-qlora-fold{f}'} for f in range(1,6)}}
        state['scheduler_pid']=os.getpid();save(state)
        event('scheduler started; max concurrent jobs=2')
        while True:
            try:
                outcome=tick(state)
            except (subprocess.TimeoutExpired,RuntimeError) as error:
                state['last_observation_error']=str(error);save(state)
                event(str(error))
                if any(j['state']=='SUBMITTING' for j in state['jobs'].values()):
                    return
                outcome='waiting'
            if args.once or outcome in ('complete','needs_diagnosis'):
                return
            time.sleep(60)


if __name__=='__main__':main()
