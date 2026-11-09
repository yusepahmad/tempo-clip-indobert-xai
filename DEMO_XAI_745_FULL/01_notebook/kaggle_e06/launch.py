import os
import subprocess
import sys
from pathlib import Path
os.environ['HF_HOME']='/kaggle/working/.cache/huggingface'
subprocess.run([sys.executable,'-m','pip','install','transformers==5.17.0','sentencepiece'],check=True,timeout=600)
# prepare.py replaces WORKER_SOURCE with the versioned worker text.
worker=Path('/kaggle/working/e06_worker.py')
worker.write_text(WORKER_SOURCE)
subprocess.run([sys.executable,'-u',str(worker)],check=True,timeout=1200)
