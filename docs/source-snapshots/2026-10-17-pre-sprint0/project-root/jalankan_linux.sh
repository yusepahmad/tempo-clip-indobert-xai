#!/usr/bin/env bash
# Menjalankan aplikasi web Demo XAI Tempo di Linux/macOS.
# Jalankan: ./jalankan_linux.sh
set -e
cd "$(dirname "$0")"

if [ ! -x venv/bin/python ]; then
  echo "Environment belum dibuat. Jalankan dulu:"
  echo "  python3.10 -m venv venv"
  echo "  venv/bin/pip install --extra-index-url https://download.pytorch.org/whl/cpu torch torchvision"
  echo "  venv/bin/pip install -r requirements.txt"
  exit 1
fi

echo "Menyalakan server. Buka http://127.0.0.1:7860 setelah siap."
echo "Tekan Ctrl+C untuk mematikan."
cd 02_web_demo
exec ../venv/bin/python app.py
