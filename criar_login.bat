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
echo   Criar um novo login no sistema
echo ============================================
echo.
set /p NOME="Nome da pessoa: "
set /p EMAIL="E-mail (sera o login): "
set /p SENHA="Senha: "
echo.
echo Perfis disponiveis:
echo   TI        = acesso total (tecnologia)
echo   RH        = acesso total (cadastra e gerencia usuarios)
echo   GESTOR    = da parecer nos candidatos
echo   DIRETORIA = somente leitura
set /p PERFIL="Perfil (TI / RH / GESTOR / DIRETORIA): "
echo.
python -m scripts.criar_admin "%NOME%" "%EMAIL%" "%SENHA%" "%PERFIL%"
echo.
echo Pronto. Use esse e-mail e senha na tela de login.
pause
