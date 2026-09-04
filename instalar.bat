@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================
echo   Instalando o sistema de RH (uma vez so)
echo ============================================
echo.
echo [1/3] Criando ambiente virtual...
py -m venv .venv 2>nul || python -m venv .venv
if not exist ".venv\Scripts\activate" (
  echo ERRO: nao consegui criar o ambiente. O Python esta instalado?
  echo Baixe em https://www.python.org/downloads/ e marque "Add Python to PATH".
  pause
  exit /b
)
call .venv\Scripts\activate

echo [2/3] Atualizando o pip...
python -m pip install --upgrade pip

echo [3/3] Instalando as bibliotecas (pode demorar 1-2 min)...
python -m pip install --upgrade "fastapi>=0.115" "uvicorn[standard]>=0.30" "sqlalchemy>=2.0.35" "pydantic>=2.9" openpyxl "python-multipart>=0.0.9"

echo.
if %errorlevel%==0 (
  echo ============================================
  echo   PRONTO! Instalacao concluida com sucesso.
  echo   Agora use o "iniciar.bat" para ligar.
  echo ============================================
) else (
  echo *** Algo deu errado na instalacao. Copie a mensagem acima e me mande. ***
)
echo.
pause
