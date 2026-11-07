"""Build/submit/observe/collect private Revisi-II tail jobs with no duplicate push."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
from datetime import datetime,timezone

HERE=Path(__file__).resolve().parent
APP=HERE.parents[1]
OUT=APP/'04_hasil_eksperimen/revisi_ii/gpu_jobs'
ORIGINAL=APP/'01_notebook/e42_tail_grid/tail_model.py'
WORKER=HERE/'tail_ablation_worker.py'


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2)+'\n')
def now():return datetime.now(timezone.utc).isoformat()
def ref(mode):return 'yusepmuhamadzazuli/tempo-revisi-ii-tail-'+mode
def build(mode):
    folder=OUT/mode/'kernel';folder.mkdir(parents=True,exist_ok=True)
    worker=WORKER.read_text();original=ORIGINAL.read_text()
    compile(worker,'worker.py','exec');compile(original,'tail_model.py','exec')
    launch="import os,sys,subprocess\nfrom pathlib import Path\n"
    launch+="os.environ['HF_HUB_OFFLINE']='1'\nos.environ['TOKENIZERS_PARALLELISM']='false'\n"
    launch+="wheel=next(Path('/kaggle/input').rglob('transformers-5.17.0-*.whl'))\nsubprocess.run([sys.executable,'-m','pip','install','--no-index','--find-links',str(wheel.parent),'transformers==5.17.0'],check=True)\n"
    launch+=f"os.environ['RII_SMOKE']={'1' if mode=='smoke' else '0'!r}\n"
    launch+=f"Path('/kaggle/working/tail_model.py').write_text({original!r})\nPath('/kaggle/working/rii_worker.py').write_text({worker!r})\n"
    launch+="subprocess.run([sys.executable,'-u','/kaggle/working/rii_worker.py'],check=True,timeout=3900)\n"
    compile(launch,'launch.py','exec');(folder/'launch.py').write_text(launch)
    metadata=json.loads((APP/'01_notebook/next_research_20261017/kaggle_ci_d01_dup2/full/kernel-metadata.json').read_text())
    metadata.update(id=ref(mode),title='Tempo Revisi II Tail '+mode.title(),code_file='launch.py',is_private=True)
    dump(folder/'kernel-metadata.json',metadata)
    dump(OUT/mode/'build_manifest.json',dict(worker_sha256=sha(WORKER),tail_model_sha256=sha(ORIGINAL),
          files={n:sha(folder/n) for n in ['launch.py','kernel-metadata.json']},created_at=now()))
    return folder


def status(mode):
    r=subprocess.run(['kaggle','kernels','status',ref(mode)],capture_output=True,text=True,timeout=90)
    match=re.search(r'KernelWorkerStatus\.([A-Z_]+)',r.stdout)
    if r.returncode or not match:raise RuntimeError((r.stderr or r.stdout)[:1000])
    record=dict(kernel=ref(mode),status=match[1],observed_at=now());dump(OUT/mode/'status.json',record);print(json.dumps(record));return match[1]


def submit(mode):
    ledger=OUT/mode/'submission.json'
    if ledger.exists():raise RuntimeError('Submission record exists; inspect status/collect instead of pushing again')
    if mode=='full':
        smoke=OUT/'smoke/raw/revisi_ii_tail_smoke/smoke.json'
        report=json.loads(smoke.read_text());assert report['status']=='passed' and len(report['checks'])==5
        old=json.loads((OUT/'smoke/build_manifest.json').read_text())
        assert old['worker_sha256']==sha(WORKER) and old['tail_model_sha256']==sha(ORIGINAL),'Source changed since smoke'
    folder=build(mode)
    dump(ledger,dict(kernel=ref(mode),state='submission_intent',created_at=now(),worker_sha256=sha(WORKER),version=1))
    r=subprocess.run(['kaggle','kernels','push','-p',str(folder)],capture_output=True,text=True,timeout=120)
    record=json.loads(ledger.read_text());record.update(state='submitted' if r.returncode==0 else 'push_ambiguous',returncode=r.returncode,stdout=r.stdout,stderr=r.stderr)
    dump(ledger,record)
    if r.returncode:raise RuntimeError((r.stderr or r.stdout)[:1500])
    print(r.stdout)


def collect(mode):
    if status(mode)!='COMPLETE':raise RuntimeError('Job is not complete')
    raw=OUT/mode/'raw';raw.mkdir(parents=True,exist_ok=True)
    if mode=='smoke':
        command=['kaggle','kernels','output',ref(mode),'-p',str(raw),'-q']
    else:
        # Preserve all predictions/audits/checkpoints on remote; local collection
        # fetches structured evidence only. Hashes of checkpoints remain in audit.
        command=['kaggle','kernels','output',ref(mode),'-p',str(raw),'-q','--file-pattern',r'.*\.(json|csv|log)$']
    r=subprocess.run(command,capture_output=True,text=True,timeout=300)
    if r.returncode:raise RuntimeError((r.stderr or r.stdout)[:2000])
    base=raw/('revisi_ii_tail_smoke' if mode=='smoke' else 'revisi_ii_tail_full')
    protocol=json.loads((base/'protocol.json').read_text())
    manifest=json.loads((OUT/mode/'build_manifest.json').read_text())
    assert protocol['source_sha256']==manifest['worker_sha256'] and protocol['tail_model_sha256']==manifest['tail_model_sha256']
    if mode=='smoke':
        result=json.loads((base/'smoke.json').read_text());assert result['status']=='passed' and len(result['checks'])==5
    else:
        result=json.loads((base/'completion.json').read_text());assert result['status']=='complete' and result['samples_each']==740
        assert result['protocol_sha256']==sha(base/'protocol.json')
        for name in result['arms']:
            folder=base/name;data=json.loads((folder/'result.json').read_text())
            assert data['status']=='complete' and data['predictions_sha256']==sha(folder/'predictions.csv')
            assert all(f['reload_identical'] and not set(f['train_indices'])&set(f['test_indices']) for f in data['folds'])
            target=APP/'04_hasil_eksperimen/revisi_ii/experiments'/name
            target.mkdir(parents=True,exist_ok=True)
            for filename in ['predictions.csv','result.json']:
                p=target/filename
                if p.exists():assert sha(p)==sha(folder/filename),'Refuse replacing a distinct completed result'
                else:shutil.copy2(folder/filename,p)
    dump(OUT/mode/'verification.json',dict(status='verified',mode=mode,protocol_sha256=sha(base/'protocol.json'),collected_at=now(),
          checkpoint_local_replay='Not Evaluated; remote FP32 reload verified, weights retained on Kaggle'))
    print('VERIFIED',mode)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['build','submit','status','collect']);ap.add_argument('mode',choices=['smoke','full']);args=ap.parse_args()
    globals()[args.action](args.mode)
