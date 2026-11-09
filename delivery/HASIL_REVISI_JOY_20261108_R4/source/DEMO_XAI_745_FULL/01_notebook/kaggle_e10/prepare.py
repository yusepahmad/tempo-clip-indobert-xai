import json
from pathlib import Path
here=Path(__file__).resolve().parent
for mode in ('smoke','full'):
    target=here/mode;target.mkdir(exist_ok=True)
    code="import os,sys,subprocess,pathlib\nos.environ['HF_HOME']='/kaggle/working/.cache/huggingface'\n"
    code+="subprocess.run([sys.executable,'-m','pip','install','transformers==5.17.0','sentencepiece'],check=True,timeout=600)\n"
    code+=f"os.environ['E10_SMOKE']={'1' if mode=='smoke' else '0'!r}\n"
    code+=f"pathlib.Path('/kaggle/working/e10_worker.py').write_text({(here/'worker.py').read_text()!r})\n"
    code+=f"subprocess.run([sys.executable,'-u','/kaggle/working/e10_worker.py'],check=True,timeout={1200 if mode=='smoke' else 4800})\n"
    (target/'launch.py').write_text(code)
    (target/'kernel-metadata.json').write_text(json.dumps({
        'id':f'research-account/tempo-e10-semantic-finetune-{mode}',
        'title':f'Tempo E10 Semantic Finetune {mode}','code_file':'launch.py',
        'language':'python','kernel_type':'script','is_private':True,'enable_gpu':True,
        'enable_internet':True,'dataset_sources':['research-account/tempo-benchmark-20261005'],
        'kernel_sources':['research-account/tempo-e01-vlm'],
        'competition_sources':[],'model_sources':[]},indent=2))
    print(target)
