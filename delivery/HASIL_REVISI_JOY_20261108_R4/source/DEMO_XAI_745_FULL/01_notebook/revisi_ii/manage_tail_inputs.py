"""Private dataset and derived E42-family input-parity jobs, immutable versions."""
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import re
import shutil
import subprocess
from evaluate import sha,write_json

HERE=Path(__file__).resolve().parent;APP=HERE.parents[1];BASE=APP/'04_hasil_eksperimen/revisi_ii'
OUT=BASE/'tail_input_jobs';DATASET='yusepmuhamadzazuli/tempo-revisi-ii-text-inputs-20261101'
REF='yusepmuhamadzazuli/tempo-revisi-ii-tail-input-'


def derive():
    source=(HERE/'tail_ablation_worker.py').read_text()
    start=source.index("ARMS=('RII_TAIL_MTL_WEIGHTED'");end=source.index('\n\n',start)
    source=source[:start]+"ARMS=('RII_TAIL_HEADLINE_ONLY','RII_TAIL_RICH256')"+source[end:]
    line='for arm in ARMS:\n'
    assert source.count(line)==2
    source=source.replace('        '+line,'        '+line+"            z=dict(np.load(next(Path('/kaggle/input').rglob('rich256_front_cache.npz' if arm=='RII_TAIL_RICH256' else 'headline_front_cache.npz'))))\n            assert z['sample_ids'].tolist()==df.sample_id.tolist()\n",1)
    source=source.replace('    '+line,'    '+line+"        z=dict(np.load(next(Path('/kaggle/input').rglob('rich256_front_cache.npz' if arm=='RII_TAIL_RICH256' else 'headline_front_cache.npz'))))\n        assert z['sample_ids'].tolist()==df.sample_id.tolist()\n",1) if False else source
    # Replace only top-level full-run arm loop, not the more-indented smoke loop.
    source=source.replace('\n    for arm in ARMS:\n','\n    for arm in ARMS:\n'+"        z=dict(np.load(next(Path('/kaggle/input').rglob('rich256_front_cache.npz' if arm=='RII_TAIL_RICH256' else 'headline_front_cache.npz'))))\n        assert z['sample_ids'].tolist()==df.sample_id.tolist()\n",1)
    source=source.replace('revisi_ii_tail_smoke','revisi_ii_tail_input_smoke').replace('revisi_ii_tail_full','revisi_ii_tail_input_full')
    source=source.replace("inputs='headline_verified [SEP] supporting_text_verified; frozen E41 cache'",
        "inputs='HEADLINE_ONLY max128 versus RICH max256; frozen CLIP features and pinned IndoBERT front; see input dataset manifests'")
    compile(source,'tail_input_worker.py','exec')
    target=HERE/'tail_input_worker.py'
    if target.exists():assert target.read_text()==source
    else:target.write_text(source)
    return target


def dataset():
    ledger=OUT/'dataset_submission.json'
    if ledger.exists():raise RuntimeError('Dataset submission record exists; do not repeat creation')
    stage=OUT/'dataset';stage.mkdir(parents=True,exist_ok=True)
    for p in [BASE/'rich256/rich256_front_cache.npz',BASE/'rich256/manifest.json',BASE/'text_inputs/headline_front_cache.npz']:
        shutil.copy2(p,stage/p.name)
    write_json(stage/'content_manifest.json',dict(files={p.name:sha(p) for p in stage.iterdir() if p.is_file()}))
    write_json(stage/'dataset-metadata.json',dict(id=DATASET,title='Tempo Revisi II Label Blind Text Inputs 20261101',licenses=[{'name':'other'}],
             description='Private experimental input cache. Model features only, no credentials, no raw gold label fields. Research scope only.'))
    write_json(ledger,dict(state='creation_intent',dataset=DATASET,private=True,created_at=datetime.now(timezone.utc).isoformat()))
    r=subprocess.run(['kaggle','datasets','create','-p',str(stage),'-q'],capture_output=True,text=True,timeout=1200)
    write_json(ledger,dict(state='created' if r.returncode==0 else 'creation_ambiguous',dataset=DATASET,private=True,output=r.stdout,stderr=r.stderr))
    if r.returncode:raise RuntimeError((r.stderr or r.stdout)[:2000])
    print(r.stdout)


def build(mode):
    worker=derive();model=APP/'01_notebook/e42_tail_grid/tail_model.py';folder=OUT/mode/'kernel';folder.mkdir(parents=True,exist_ok=True)
    launch="import os,sys,subprocess\nfrom pathlib import Path\nos.environ['HF_HUB_OFFLINE']='1'\n"
    launch+="wheel=next(Path('/kaggle/input').rglob('transformers-5.17.0-*.whl'))\nsubprocess.run([sys.executable,'-m','pip','install','--no-index','--find-links',str(wheel.parent),'transformers==5.17.0'],check=True)\n"
    launch+=f"os.environ['RII_SMOKE']={'1' if mode=='smoke' else '0'!r}\n"
    launch+=f"Path('/kaggle/working/tail_model.py').write_text({model.read_text()!r})\nPath('/kaggle/working/tail_input_worker.py').write_text({worker.read_text()!r})\n"
    launch+="subprocess.run([sys.executable,'-u','/kaggle/working/tail_input_worker.py'],check=True,timeout=3900)\n"
    compile(launch,'launch.py','exec');(folder/'launch.py').write_text(launch)
    metadata=json.loads((BASE/'gpu_jobs/full/kernel/kernel-metadata.json').read_text())
    metadata.update(id=REF+mode,title='Tempo Revisi II Tail Input '+mode.title(),is_private=True,dataset_sources=metadata['dataset_sources']+[DATASET])
    write_json(folder/'kernel-metadata.json',metadata)
    write_json(OUT/mode/'build_manifest.json',dict(worker_sha256=sha(worker),base_worker_sha256=sha(HERE/'tail_ablation_worker.py'),tail_model_sha256=sha(model)))
    return folder


def status(mode):
    r=subprocess.run(['kaggle','kernels','status',REF+mode],capture_output=True,text=True,timeout=90)
    m=re.search(r'KernelWorkerStatus\.([A-Z_]+)',r.stdout)
    if r.returncode or not m:raise RuntimeError((r.stderr or r.stdout)[:1000])
    value=dict(kernel=REF+mode,status=m[1],observed_at=datetime.now(timezone.utc).isoformat());write_json(OUT/mode/'status.json',value);print(json.dumps(value));return m[1]


def submit(mode):
    ledger=OUT/mode/'submission.json'
    if ledger.exists():raise RuntimeError('Submission record exists; inspect status/collect')
    if mode=='full':
        v=json.loads((OUT/'smoke/verification.json').read_text());assert v['status']=='verified' and v['worker_sha256']==sha(derive())
    path=build(mode);write_json(ledger,dict(state='submission_intent',version=1,kernel=REF+mode))
    r=subprocess.run(['kaggle','kernels','push','-p',str(path)],capture_output=True,text=True,timeout=120)
    write_json(ledger,dict(state='submitted' if r.returncode==0 else 'push_ambiguous',version=1,kernel=REF+mode,output=r.stdout,stderr=r.stderr))
    if r.returncode:raise RuntimeError((r.stderr or r.stdout)[:1500])
    print(r.stdout)


def collect(mode):
    if status(mode)!='COMPLETE':raise RuntimeError('Job not complete')
    raw=OUT/mode/'raw';raw.mkdir(parents=True,exist_ok=True)
    r=subprocess.run(['kaggle','kernels','output',REF+mode,'-p',str(raw),'-q','--file-pattern',r'.*\.(json|csv)$'],capture_output=True,text=True,timeout=300)
    if r.returncode:raise RuntimeError((r.stderr or r.stdout)[:1500])
    folder=raw/('revisi_ii_tail_input_smoke' if mode=='smoke' else 'revisi_ii_tail_input_full')
    protocol=json.loads((folder/'protocol.json').read_text());manifest=json.loads((OUT/mode/'build_manifest.json').read_text())
    assert protocol['source_sha256']==manifest['worker_sha256']
    if mode=='smoke':
        result=json.loads((folder/'smoke.json').read_text());assert result['status']=='passed' and len(result['checks'])==2
    else:
        result=json.loads((folder/'completion.json').read_text());assert result['status']=='complete' and result['samples_each']==740
        for name in result['arms']:
            arm=folder/name;record=json.loads((arm/'result.json').read_text());assert record['status']=='complete' and sha(arm/'predictions.csv')==record['predictions_sha256']
            assert all(f['reload_identical'] for f in record['folds'])
            dest=BASE/'experiments'/name;dest.mkdir(parents=True,exist_ok=True)
            for filename in ['result.json','predictions.csv']:
                if (dest/filename).exists():assert sha(dest/filename)==sha(arm/filename)
                else:shutil.copy2(arm/filename,dest/filename)
    write_json(OUT/mode/'verification.json',dict(status='verified',worker_sha256=manifest['worker_sha256'],protocol_sha256=sha(folder/'protocol.json')))
    print('TAIL INPUT VERIFIED',mode)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['dataset','build','submit','status','collect']);ap.add_argument('mode',nargs='?',choices=['smoke','full'],default='smoke');a=ap.parse_args()
    dataset() if a.action=='dataset' else globals()[a.action](a.mode)
