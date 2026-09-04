@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
title Baixar bibliotecas para dentro do sistema

if not exist ".venv\Scripts\activate" (
  echo.
  echo   Rode o "instalar.bat" primeiro.
  echo.
  pause
  exit /b 1
)
call .venv\Scripts\activate

echo ============================================
echo   Deixar o sistema independente da internet
echo ============================================
echo.
echo   Hoje o sistema baixa React, Babel e Tailwind da
echo   internet toda vez que a pagina abre. Se a rede
echo   bloquear ou o site sair do ar, a tela fica branca.
echo.
echo   Este passo traz essas bibliotecas para dentro do
echo   projeto. Precisa de internet AGORA, uma unica vez.
echo.
pause
echo.

python -m scripts.baixar_bibliotecas
set "CODIGO=%ERRORLEVEL%"

echo.
if not "!CODIGO!"=="0" (
  echo   Algo ficou faltando. Veja as mensagens acima.
) else (
  echo   Feche o "iniciar.bat" e abra de novo.
)
echo.
pause
exit /b !CODIGO!
