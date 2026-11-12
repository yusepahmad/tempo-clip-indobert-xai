#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-8}" MKL_NUM_THREADS="${MKL_NUM_THREADS:-8}"
export TEMPO_BACKEND="${TEMPO_BACKEND:-e42-tail-grid}"
PYTHON_BIN="${TEMPO_PYTHON:-venv/bin/python}"
if [[ "$TEMPO_BACKEND" == "e42-tail-grid" ]]; then
    "$PYTHON_BIN" 01_notebook/check_delivery.py
fi
exec "$PYTHON_BIN" -u 02_web_demo/app.py
