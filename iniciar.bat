@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
title ATS TLM - servidor ligado (nao feche esta janela)

set "PORTA=8000"
set "ENDERECO=http://localhost:%PORTA%"

if not exist ".venv\Scripts\activate" (
  echo.
  echo   Ambiente nao encontrado. Rode o "instalar.bat" primeiro.
  echo.
  pause
  exit /b 1
)
call .venv\Scripts\activate

rem --- alguem ja esta usando a porta? (servidor esquecido aberto) ---
set "OCUPADA="
for /f "tokens=5" %%p in ('netstat -ano ^| findstr /r /c:"LISTENING" ^| findstr ":%PORTA% "') do set "OCUPADA=%%p"
if defined OCUPADA (
  echo ============================================
  echo   A porta %PORTA% JA ESTA EM USO
  echo ============================================
  echo.
  echo   Provavelmente o sistema ja esta ligado em outra janela.
  echo.
  echo   Abra no navegador:  %ENDERECO%
  echo.
  echo   Se a pagina nao carregar, feche a outra janela preta
  echo   e rode este arquivo de novo.
  echo.
  start "" "%ENDERECO%"
  pause
  exit /b 0
)

cls
echo ============================================
echo   ATS TLM - Recrutamento
echo ============================================
echo.
echo   Endereco do sistema:
echo       %ENDERECO%
echo.
echo   (a documentacao tecnica da API fica em %ENDERECO%/docs
echo    - nao e por ali que o RH entra)
echo.
echo   NAO FECHE ESTA JANELA enquanto estiver usando.
echo   Para desligar: Ctrl+C, ou feche a janela.
echo ============================================
echo.

rem abre o navegador sozinho depois de 3s, ja no endereco certo
start "" cmd /c "timeout /t 3 >nul & start """" ""%ENDERECO%"""

python -m uvicorn app.main:app --host 127.0.0.1 --port %PORTA%
set "CODIGO=%ERRORLEVEL%"

echo.
echo ============================================
if not "!CODIGO!"=="0" (
  echo   O SERVIDOR PAROU COM ERRO  [codigo !CODIGO!]
  echo.
  echo   Leia a mensagem acima. Causas comuns:
  echo     - porta %PORTA% ocupada por outra janela
  echo     - banco de dados em uso ou corrompido
  echo     - falta de dependencia: rode o "instalar.bat"
) else (
  echo   Servidor desligado.
)
echo ============================================
echo.
pause
exit /b !CODIGO!
