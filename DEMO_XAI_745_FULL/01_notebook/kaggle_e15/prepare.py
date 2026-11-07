import ast
import json
from pathlib import Path

here=Path(__file__).resolve().parent
tree=ast.parse((here.parent/'kaggle_e12/worker.py').read_text())
nodes=[n for n in tree.body if
       (isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='DEFINITIONS' for t in n.targets))
       or (isinstance(n,ast.FunctionDef) and n.name=='build_prompt')]
assert len(nodes)==2
helper='\n\n'.join(ast.unparse(n) for n in nodes)+'\n'
(here/'prompt.py').write_text(helper)
target=here/'full';target.mkdir(exist_ok=True)
code="import os,sys,subprocess,pathlib\nos.environ['HF_HOME']='/kaggle/working/.cache/huggingface'\n"
code+="subprocess.run([sys.executable,'-m','pip','install','transformers==5.17.0','accelerate==1.15.0'],check=True,timeout=600)\n"
code+=f"pathlib.Path('/kaggle/working/e15_prompt.py').write_text({helper!r})\n"
code+=f"pathlib.Path('/kaggle/working/e15_worker.py').write_text({(here/'worker.py').read_text()!r})\n"
code+="subprocess.run([sys.executable,'-u','/kaggle/working/e15_worker.py'],check=True,timeout=3000)\n"
(target/'launch.py').write_text(code)
(target/'kernel-metadata.json').write_text(json.dumps({
    'id':'yusepmuhamadzazuli/tempo-e15-vlm-features','title':'Tempo E15 Vlm Features','code_file':'launch.py',
    'language':'python','kernel_type':'script','is_private':True,'enable_gpu':True,'enable_internet':True,
    'dataset_sources':['yusepmuhamadzazuli/tempo-benchmark-20261005'],
    'kernel_sources':['yusepmuhamadzazuli/tempo-e01-vlm'],
    'competition_sources':[],'model_sources':[]},indent=2))
