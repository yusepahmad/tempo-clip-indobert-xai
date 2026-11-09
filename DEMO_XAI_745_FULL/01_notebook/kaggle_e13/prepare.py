import json
from pathlib import Path
here=Path(__file__).resolve().parent
target=here/'full';target.mkdir(exist_ok=True)
code="import os,sys,subprocess,pathlib\nos.environ['HF_HOME']='/kaggle/working/.cache/huggingface'\n"
code+="subprocess.run([sys.executable,'-m','pip','install','transformers==5.17.0'],check=True,timeout=600)\n"
code+=f"pathlib.Path('/kaggle/working/e13_worker.py').write_text({(here/'worker.py').read_text()!r})\n"
code+="subprocess.run([sys.executable,'-u','/kaggle/working/e13_worker.py'],check=True,timeout=1200)\n"
(target/'launch.py').write_text(code)
(target/'kernel-metadata.json').write_text(json.dumps({
    'id':'research-account/tempo-e13-bge-m3','title':'Tempo E13 Bge M3','code_file':'launch.py',
    'language':'python','kernel_type':'script','is_private':True,'enable_gpu':True,'enable_internet':True,
    'dataset_sources':['research-account/tempo-benchmark-20261005'],
    'kernel_sources':['research-account/tempo-e01-vlm'],
    'competition_sources':[],'model_sources':[]},indent=2))
