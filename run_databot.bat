@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Сначала создай окружение: py -3.9 -m venv .venv
  pause
  exit /b 1
)
".venv\Scripts\python.exe" -m streamlit run app.py
pause
