@echo off
setlocal
cd /d "%~dp0"

echo ==========================================================
echo   SETUP DEMO XAI TEMPO E42 - WINDOWS
echo ==========================================================
echo.

echo [1/4] Mencari Python 3.10 atau 3.11 ...
set "PY="
py -3.10 --version >nul 2>&1 && set "PY=py -3.10"
if not defined PY py -3.11 --version >nul 2>&1 && set "PY=py -3.11"
if not defined PY (
    for /f "tokens=2" %%v in ('python --version 2^>^&1') do (
        echo %%v | findstr /b "3.10 3.11" >nul && set "PY=python"
    )
)
if not defined PY (
    echo.
    echo   GAGAL: Python 3.10 atau 3.11 tidak ditemukan.
    echo   Unduh Python dari https://www.python.org/downloads/
    echo   dan centang opsi Add Python to PATH serta py launcher.
    echo.
    pause
    exit /b 1
)
echo       ditemukan: %PY%
echo.

echo [2/4] Membuat environment terpisah di folder venv ...
if exist "venv\Scripts\python.exe" (
    echo       folder venv sudah ada, dipakai ulang.
) else (
    %PY% -m venv venv
    if errorlevel 1 (
        echo   GAGAL membuat venv. Periksa instalasi Python.
        pause
        exit /b 1
    )
)
set "PYTHON_EXE=venv\Scripts\python.exe"
echo.

echo [3/4] Memasang dependency serving yang dikunci ...
echo       Proses ini memerlukan internet dan dapat memakan waktu.
"%PYTHON_EXE%" -m pip install --upgrade pip
if errorlevel 1 goto :install_error
"%PYTHON_EXE%" -m pip install -r "02_web_demo\requirements-web-lock.txt"
if errorlevel 1 goto :install_error
echo.

echo [4/4] Memeriksa lima checkpoint dan 740 prediksi E42 ...
"%PYTHON_EXE%" "01_notebook\check_delivery.py"
if errorlevel 1 (
    echo.
    echo   GAGAL: aset E42 tidak lengkap atau tidak cocok.
    pause
    exit /b 1
)

echo.
echo ==========================================================
echo   SETUP DAN PEMERIKSAAN E42 SELESAI
echo ==========================================================
echo.
echo   Jalankan aplikasi dengan klik dua kali jalankan_windows.bat
echo.
echo   Pada analisis pertama, aplikasi mengunduh backbone publik
echo   CLIP-L14, IndoBERT, dan EasyOCR. Siapkan internet dan ruang
echo   disk beberapa GB; unduhan berikutnya dibaca dari cache.
echo.
pause
exit /b 0

:install_error
echo.
echo   GAGAL memasang dependency serving.
echo   Periksa koneksi internet. Jika ada galat long path, aktifkan
echo   dukungan path panjang Windows atau pindahkan ke C:\demo_xai.
echo.
pause
exit /b 1
