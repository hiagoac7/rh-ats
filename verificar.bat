@echo off
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
if not exist ".venv\Scripts\activate" (
  echo Rode o "instalar.bat" primeiro.
  pause
  exit /b
)
call .venv\Scripts\activate
python scripts\verificar.py
echo.
pause
