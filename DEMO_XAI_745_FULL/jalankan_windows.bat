@echo off
cd /d "%~dp0"
set TEMPO_BACKEND=clip-indobert-mtl
set OMP_NUM_THREADS=8
set MKL_NUM_THREADS=8
venv\Scripts\python.exe 01_notebook\check_delivery.py
if errorlevel 1 exit /b 1
venv\Scripts\python.exe 02_web_demo\app.py
