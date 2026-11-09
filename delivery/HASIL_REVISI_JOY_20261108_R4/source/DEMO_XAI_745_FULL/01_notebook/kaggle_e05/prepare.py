"""Build reproducible private smoke/full kernels from the same worker."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
worker=(HERE/'worker.py').read_text()
for mode in ('smoke','full'):
    folder=HERE/mode
    folder.mkdir(exist_ok=True)
    launcher='''import os, pathlib, subprocess, sys
os.environ['HF_HUB_OFFLINE']='1'
os.environ['TOKENIZERS_PARALLELISM']='false'
paths=list(pathlib.Path('/kaggle/input').rglob('DATASET_740_TASK2_DOMAIN.csv'))
assert len(paths)==1, 'Benchmark dataset CSV must be mounted'
root=paths[0].parents[1]
subprocess.run([sys.executable,'-m','pip','install','--no-index','--find-links',str(root/'wheels'),'open_clip_torch==3.3.0','transformers==5.17.0'],check=True,timeout=900)
'''
    launcher+=f"os.environ['TEMPO_E05_SMOKE']={'1' if mode=='smoke' else '0'!r}\n"
    launcher+=f"pathlib.Path('/kaggle/working/e05_worker.py').write_text({worker!r})\n"
    launcher+=f"subprocess.run([sys.executable,'-u','/kaggle/working/e05_worker.py'],check=True,timeout={1800 if mode=='smoke' else 9000})\n"
    (folder/'launch.py').write_text(launcher)
    meta={'id':f'research-account/tempo-e05-task2-{mode}',
          'title':f'Tempo E05 Task2 {mode}', 'code_file':'launch.py',
          'language':'python','kernel_type':'script','is_private':True,
          'enable_gpu':True,'enable_internet':False,
          'dataset_sources':['research-account/tempo-benchmark-20261005'],
          'competition_sources':[],'kernel_sources':[],'model_sources':[]}
    (folder/'kernel-metadata.json').write_text(json.dumps(meta,indent=2))
    print(mode,hashlib.sha256(launcher.encode()).hexdigest())
