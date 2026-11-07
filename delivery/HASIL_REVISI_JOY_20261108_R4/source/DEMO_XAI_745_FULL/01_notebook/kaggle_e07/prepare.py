import json
from pathlib import Path
here=Path(__file__).resolve().parent
for mode in ('smoke','full'):
    target=here/mode;target.mkdir(exist_ok=True)
    code="import os,sys,subprocess,pathlib\nos.environ['HF_HOME']='/kaggle/working/.cache/huggingface'\n"
    code+="subprocess.run([sys.executable,'-m','pip','install','transformers==5.17.0','accelerate'],check=True,timeout=900)\n"
    code+=f"os.environ['E07_SMOKE']={'1' if mode=='smoke' else '0'!r}\n"
    code+=f"pathlib.Path('/kaggle/working/e07_worker.py').write_text({(here/'worker.py').read_text()!r})\n"
    code+=f"subprocess.run([sys.executable,'-u','/kaggle/working/e07_worker.py'],check=True,timeout={1800 if mode=='smoke' else 7200})\n"
    (target/'launch.py').write_text(code)
    (target/'kernel-metadata.json').write_text(json.dumps({
        'id':f'yusepmuhamadzazuli/tempo-e07-fewshot-{mode}','title':f'Tempo E07 Fewshot {mode}',
        'code_file':'launch.py','language':'python','kernel_type':'script','is_private':True,
        'enable_gpu':True,'enable_internet':True,
        'dataset_sources':['yusepmuhamadzazuli/tempo-benchmark-20261005'],
        'kernel_sources':['yusepmuhamadzazuli/tempo-e01-vlm'],
        'competition_sources':[],'model_sources':[]},indent=2))
    print(target)
