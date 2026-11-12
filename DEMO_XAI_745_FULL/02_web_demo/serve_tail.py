#!/usr/bin/env python3
"""Run from the pinned web environment; no runtime training or online downloads."""
import os
from pathlib import Path
HERE = Path(__file__).resolve().parent
os.chdir(HERE)
os.environ.setdefault('TEMPO_BACKEND', 'e42-tail-grid')
os.environ.setdefault('HF_HUB_OFFLINE', '1')
os.environ.setdefault('TOKENIZERS_PARALLELISM', 'false')
for key in ['OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS']:
    os.environ.setdefault(key, '4')
import sys
os.execv(sys.executable, [sys.executable, '-m', 'gunicorn', '-c', str(HERE/'gunicorn_conf.py'), 'app:app'])
