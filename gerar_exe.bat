@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist ".venv\Scripts\activate" (
  echo Rode o "instalar.bat" primeiro.
  pause
  exit /b
)
call .venv\Scripts\activate
echo ============================================
echo   Gerando o programa (.exe)
echo   Pode levar de 2 a 5 minutos.
echo ============================================
echo.
pip install --upgrade pyinstaller
pyinstaller --noconfirm --onefile --name "ATS-TLM" ^
  --icon "ats.ico" ^
  --add-data "app/static;app/static" ^
  --add-data "migrations;migrations" ^
  --add-data "alembic.ini;." ^
  --hidden-import "uvicorn.logging" ^
  --hidden-import "uvicorn.loops.auto" ^
  --hidden-import "uvicorn.protocols.http.auto" ^
  --hidden-import "uvicorn.protocols.websockets.auto" ^
  --hidden-import "uvicorn.lifespan.on" ^
  scripts\app_desktop.py
echo.
if exist "dist\ATS-TLM.exe" (
  echo ============================================
  echo   PRONTO: dist\ATS-TLM.exe
  echo.
  echo   IMPORTANTE: o banco fica na mesma pasta do
  echo   .exe. Se cada pessoa rodar o seu, os dados
  echo   NAO serao compartilhados.
  echo   Para uso em equipe, use o servidor +
  echo   "criar_atalho.bat".
  echo ============================================
) else (
  echo *** Algo deu errado. Copie a mensagem acima. ***
)
echo.
pause
