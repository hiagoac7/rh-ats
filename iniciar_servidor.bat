@echo off
chcp 65001 >nul
cd /d "%~dp0"
title ATS TLM - servidor
if not exist ".venv\Scripts\activate" (
  echo Rode o "instalar.bat" primeiro.
  pause
  exit /b
)
call .venv\Scripts\activate
echo ============================================
echo   ATS TLM — servidor ligado
echo ============================================
echo.
echo   Neste computador ....: http://localhost:8000
echo   Na rede da empresa ..:
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
  for /f "tokens=* delims= " %%b in ("%%a") do echo         http://%%b:8000
)
echo   Fora da empresa .....: depende do tunel/servidor (veja ACESSO_EXTERNO.md)
echo.
echo   IMPORTANTE: deixe esta janela aberta enquanto a equipe usa.
echo   Para desligar: feche a janela ou aperte Ctrl+C
echo ============================================
echo.
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
pause
