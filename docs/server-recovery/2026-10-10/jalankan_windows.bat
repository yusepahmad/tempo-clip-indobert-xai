@echo off
REM ===================================================================
REM  Menjalankan aplikasi web Demo XAI Tempo di Windows
REM  Klik dua kali berkas ini.
REM  Jalankan setup_windows.bat lebih dulu bila belum pernah.
REM ===================================================================

setlocal
cd /d "%~dp0"

if not exist venv\Scripts\python.exe (
    echo.
    echo   Environment belum dibuat.
    echo   Jalankan setup_windows.bat lebih dulu.
    echo.
    pause
    exit /b 1
)

echo ==========================================================
echo   DEMO XAI TEMPO
echo ==========================================================
echo.
echo   Menyalakan server ...
echo.
echo   Saat PERTAMA kali, model diunduh (sekitar 1,5 GB) sehingga
echo   proses ini bisa memakan beberapa menit. Selanjutnya cepat.
echo.
echo   Setelah muncul tulisan "Running on http://127.0.0.1:7860",
echo   buka alamat itu di peramban (port baku aplikasi 7860).
echo.
echo   Tekan Ctrl+C di jendela ini untuk mematikan server.
echo ==========================================================
echo.

cd 02_web_demo
..\venv\Scripts\python app.py

pause
