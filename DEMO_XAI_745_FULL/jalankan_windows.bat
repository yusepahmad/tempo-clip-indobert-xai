@echo off
setlocal
cd /d "%~dp0"

if not defined TEMPO_BACKEND set "TEMPO_BACKEND=e42-tail-grid"
if not defined OMP_NUM_THREADS set "OMP_NUM_THREADS=8"
if not defined MKL_NUM_THREADS set "MKL_NUM_THREADS=8"
set "PYTHON_EXE=venv\Scripts\python.exe"

if not exist "%PYTHON_EXE%" (
    echo.
    echo   GAGAL: environment Python belum tersedia.
    echo   Jalankan setup_windows.bat terlebih dahulu.
    echo.
    pause
    exit /b 1
)

echo Memeriksa aset model E42 ...
"%PYTHON_EXE%" "01_notebook\check_delivery.py"
if errorlevel 1 (
    echo.
    echo   GAGAL: pemeriksaan aset E42 tidak lulus.
    echo   Lihat pesan galat di atas sebelum menjalankan aplikasi.
    echo.
    pause
    exit /b 1
)

echo Menjalankan aplikasi dengan backend %TEMPO_BACKEND% ...
"%PYTHON_EXE%" -u "02_web_demo\app.py"
if errorlevel 1 (
    echo.
    echo   Aplikasi berhenti karena galat.
    pause
    exit /b 1
)
