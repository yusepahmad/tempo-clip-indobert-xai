#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-8}" MKL_NUM_THREADS="${MKL_NUM_THREADS:-8}"
export TEMPO_BACKEND=clip-indobert-mtl
PYTHON_BIN="${TEMPO_PYTHON:-venv/bin/python}"
"$PYTHON_BIN" 01_notebook/check_delivery.py
exec "$PYTHON_BIN" -u 02_web_demo/app.py
