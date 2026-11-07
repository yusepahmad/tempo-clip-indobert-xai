#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
export TEMPO_BACKEND=micro-e14-qlora
export TEMPO_PORT="${TEMPO_PORT:-7861}"
PYTHON_BIN="${TEMPO_PYTHON:-venv-e14/bin/python}"
exec "$PYTHON_BIN" -u 02_web_demo/app.py
