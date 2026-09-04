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
echo ============================================
echo   Aplicando migrations no banco (alembic)
echo ============================================
echo.
alembic upgrade head
echo.
echo Se apareceu "Running upgrade -> 0001", deu certo.
pause
