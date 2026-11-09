@echo off
cd /d "%~dp0"
set TEMPO_BACKEND=micro-e14-qlora
if not defined TEMPO_PORT set TEMPO_PORT=7861
if not defined TEMPO_PYTHON set TEMPO_PYTHON=venv-e14\Scripts\python.exe
"%TEMPO_PYTHON%" -u 02_web_demo/app.py
pause
