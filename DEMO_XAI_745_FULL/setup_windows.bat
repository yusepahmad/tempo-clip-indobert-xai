@echo off
REM ===================================================================
REM  Setup otomatis untuk Windows
REM  Demo XAI - Dekoding Metafora Sampul Majalah Tempo
REM
REM  Klik dua kali berkas ini, atau jalankan dari Command Prompt.
REM  Cukup dijalankan SEKALI. Setelah itu pakai jalankan_windows.bat
REM ===================================================================

setlocal
cd /d "%~dp0"

echo ==========================================================
echo   SETUP DEMO XAI TEMPO - WINDOWS
echo ==========================================================
echo.

REM --- 1. Cari Python 3.10 atau 3.11 -------------------------------
echo [1/4] Mencari Python 3.10 atau 3.11 ...

set PY=
py -3.10 --version >nul 2>&1 && set PY=py -3.10
if not defined PY py -3.11 --version >nul 2>&1 && set PY=py -3.11

if not defined PY (
    for /f "tokens=2" %%v in ('python --version 2^>^&1') do (
        echo %%v | findstr /b "3.10 3.11" >nul && set PY=python
    )
)

if not defined PY (
    echo.
    echo   GAGAL: Python 3.10 atau 3.11 tidak ditemukan.
    echo.
    echo   PyTorch belum mendukung Python 3.12 ke atas, jadi versi
    echo   tersebut TIDAK bisa dipakai.
    echo.
    echo   Unduh Python 3.10 di:
    echo     https://www.python.org/downloads/release/python-31011/
    echo.
    echo   Saat memasang, CENTANG dua opsi ini:
    echo     [x] Add Python to PATH
    echo     [x] py launcher
    echo.
    pause
    exit /b 1
)
echo       ditemukan: %PY%
echo.

REM --- 2. Buat virtual environment ---------------------------------
echo [2/4] Membuat environment terpisah (folder venv) ...
if exist venv\Scripts\python.exe (
    echo       folder venv sudah ada, dipakai ulang.
) else (
    %PY% -m venv venv
    if errorlevel 1 (
        echo.
        echo   GAGAL membuat venv. Periksa instalasi Python.
        pause
        exit /b 1
    )
    echo       selesai.
)
echo.

REM --- 3. Pasang PyTorch versi CPU ---------------------------------
echo [3/4] Memasang PyTorch (unduhan besar, sekitar 200 MB) ...
echo       Mohon tunggu, jangan tutup jendela ini.
venv\Scripts\python -m pip install --upgrade pip --quiet
venv\Scripts\pip install --extra-index-url https://download.pytorch.org/whl/cpu torch torchvision
if errorlevel 1 (
    echo.
    echo   GAGAL memasang PyTorch.
    echo   Bila muncul galat soal "long path", aktifkan dukungan path
    echo   panjang di Windows, atau pindahkan folder ini ke C:\demo_xai
    pause
    exit /b 1
)
echo.

REM --- 4. Pasang pustaka lain --------------------------------------
echo [4/4] Memasang pustaka lain (transformers, flask, easyocr, ...) ...
venv\Scripts\pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo   GAGAL memasang pustaka. Periksa koneksi internet.
    pause
    exit /b 1
)

echo.
echo ==========================================================
echo   SETUP SELESAI
echo ==========================================================
echo.
echo   Jalankan aplikasi dengan klik dua kali:
echo       jalankan_windows.bat
echo.
echo   Catatan: saat PERTAMA kali dijalankan, aplikasi mengunduh
echo   model CLIP, IndoBERT, dan EasyOCR (total sekitar 1,5 GB).
echo   Unduhan ini hanya sekali; selanjutnya dibaca dari cache.
echo.
echo   requirements-verification.txt dan requirements-browser.txt
echo   hanya untuk test/verifikasi, tidak dibutuhkan aplikasi.
echo.
pause
