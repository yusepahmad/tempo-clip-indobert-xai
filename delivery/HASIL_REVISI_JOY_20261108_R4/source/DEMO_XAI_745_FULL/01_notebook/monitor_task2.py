"""Single durable watcher: inspect existing runs; never restart Kaggle kernels."""
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from datetime import datetime,timezone

ROOT=Path(__file__).resolve().parents[1]
LEARN=ROOT.parent
OUT=ROOT/'04_hasil_eksperimen/task2_monitor'
OUT.mkdir(parents=True,exist_ok=True)
lock=(OUT/'monitor.lock').open('w')
fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
lock.write(str(os.getpid()));lock.flush()
CLI=LEARN/'.kaggle/cli/bin/kaggle'
ENV={**os.environ,'KAGGLE_CONFIG_DIR':str(LEARN/'.kaggle')}
SLUGS={'e05':'yusepmuhamadzazuli/tempo-e05-task2-full',
       'e06':'yusepmuhamadzazuli/tempo-e06-semantic'}
DEST={'e05':ROOT/'04_hasil_eksperimen/e05_full',
      'e06':ROOT/'04_hasil_eksperimen/e06_semantic'}
state={'pid':os.getpid(),'runs':{},'evaluation':None}
evaluation=None
evaluation_log=None
downloaded=set()

def record(message):
    row={'at':datetime.now(timezone.utc).isoformat(),**message}
    with (OUT/'history.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
    print(json.dumps(row),flush=True)

def call(args,timeout=60):
    return subprocess.run([str(CLI),*args],env=ENV,capture_output=True,text=True,timeout=timeout)

while True:
    for name,slug in SLUGS.items():
        try:
            response=call(['kernels','status',slug])
            text=response.stdout+response.stderr
            status=next((s for s in ['COMPLETE','ERROR','CANCELLED','CANCELED','RUNNING','QUEUED']
                         if 'KernelWorkerStatus.'+s in text),None)
            if response.returncode or status is None:
                record({'run':name,'observation_error':text[-2000:]})
                continue
            state['runs'][name]=status
            record({'run':name,'status':status})
            if status in ('COMPLETE','ERROR','CANCELLED','CANCELED') and name not in downloaded:
                DEST[name].mkdir(parents=True,exist_ok=True)
                r=call(['kernels','output',slug,'-p',str(DEST[name]),
                        '--file-pattern',r'.*\.(json|jsonl|csv|log|npz)$'],timeout=300)
                record({'run':name,'download_exit':r.returncode,'download_output':(r.stdout+r.stderr)[-5000:]})
                if r.returncode==0:downloaded.add(name)
        except subprocess.TimeoutExpired:
            record({'run':name,'observation_error':'CLI timeout; existing kernel retained'})
        except Exception as error:
            record({'run':name,'observation_error':str(error)})
    if 'e06' in downloaded and evaluation is None and state['evaluation'] is None:
        candidates=list(DEST['e06'].rglob('embeddings.npz'))
        if len(candidates)==1 and (candidates[0].parent/'meta.json').is_file():
            evaluation_log=(OUT/'e06_evaluation.log').open('a')
            evaluation=subprocess.Popen([sys.executable,'-u',str(ROOT/'01_notebook/kaggle_e06/evaluate.py'),
                str(candidates[0].parent)],stdout=evaluation_log,stderr=subprocess.STDOUT)
            state['evaluation']={'status':'running','pid':evaluation.pid}
            record({'e06_evaluation_started':evaluation.pid})
        else:
            state['evaluation']={'status':'missing_embeddings','candidates':len(candidates)}
            record({'e06_evaluation':'not_started_missing_embeddings'})
    if evaluation is not None and evaluation.poll() is not None:
        code=evaluation.wait();evaluation_log.close()
        state['evaluation']={'status':'complete' if code==0 else 'error','exit_code':code}
        record({'e06_evaluation_exit':code})
        evaluation=None
    state['updated_at']=datetime.now(timezone.utc).isoformat()
    (OUT/'status.json').write_text(json.dumps(state,indent=2))
    if len(downloaded)==len(SLUGS) and state['evaluation'] is not None and state['evaluation'].get('status')!='running':
        record({'monitor':'finished_existing_runs'})
        break
    time.sleep(60)
