import json
from pathlib import Path
here=Path(__file__).resolve().parent
for mode in ('smoke','fold1','fold2','fold3','fold4','fold5'):
    target=here/mode;target.mkdir(exist_ok=True)
    smoke=mode=='smoke';fold=1 if smoke else int(mode[-1])
    code="import os,sys,subprocess,pathlib\nos.environ['HF_HOME']='/kaggle/working/.cache/huggingface'\n"
    code+="subprocess.run([sys.executable,'-m','pip','install','transformers==5.17.0','peft==0.21.2','bitsandbytes==0.50.2','accelerate==1.15.0'],check=True,timeout=900)\n"
    code+=f"os.environ['E12_SMOKE']={'1' if smoke else '0'!r}\nos.environ['E12_FOLD']={str(fold)!r}\n"
    code+=f"pathlib.Path('/kaggle/working/e12_worker.py').write_text({(here/'worker.py').read_text()!r})\n"
    code+=f"subprocess.run([sys.executable,'-u','/kaggle/working/e12_worker.py'],check=True,timeout={2700 if smoke else 27600})\n"
    (target/'launch.py').write_text(code)
    (target/'kernel-metadata.json').write_text(json.dumps({
        'id':f'yusepmuhamadzazuli/tempo-e12-qlora-{mode}',
        'title':f'Tempo E12 Qlora {mode.title()}','code_file':'launch.py','language':'python',
        'kernel_type':'script','is_private':True,'enable_gpu':True,'enable_internet':True,
        'dataset_sources':['yusepmuhamadzazuli/tempo-benchmark-20261005'],
        'kernel_sources':['yusepmuhamadzazuli/tempo-e01-vlm'],
        'competition_sources':[],'model_sources':[]},indent=2))
    print(target)
