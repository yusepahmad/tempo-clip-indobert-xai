#!/usr/bin/env bash
# Menjalankan aplikasi web Demo XAI Tempo di Linux/macOS.
# Jalankan: ./jalankan_linux.sh
set -e
cd "$(dirname "$0")"

if [ ! -x venv/bin/python ]; then
  echo "Environment belum dibuat. Jalankan dulu (Python 3.10 atau 3.11):"
  echo "  python3.10 -m venv venv        # atau python3.11"
  echo "  venv/bin/pip install --extra-index-url https://download.pytorch.org/whl/cpu torch torchvision"
  echo "  venv/bin/pip install -r requirements.txt"
  echo "Opsional: requirements-lock-linux.txt untuk versi persis yang sudah diuji"
  echo "(lihat komentar di berkas itu); requirements-verification.txt dan"
  echo "requirements-browser.txt hanya untuk test/verifikasi, tidak dibutuhkan aplikasi."
  exit 1
fi

echo "Menyalakan server. Buka http://127.0.0.1:7860 setelah muncul 'Running on'."
echo "Saat pertama kali, model CLIP, IndoBERT dan EasyOCR diunduh (sekitar 1,5 GB)."
echo "Tekan Ctrl+C untuk mematikan."
cd 02_web_demo
exec ../venv/bin/python app.py
