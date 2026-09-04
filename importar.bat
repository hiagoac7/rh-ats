@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
title Importar dados da planilha

rem ATENCAO PARA QUEM FOR MEXER AQUI:
rem Planilha baixada do Drive costuma vir com parenteses no nome, tipo
rem "Automacao_RH_v17 (2).xlsx". Dentro de um bloco  if ( ... )  o cmd expande
rem a variavel ANTES de executar, entao um %ARQ% SEM ASPAS faz o ")" do "(2)"
rem fechar o bloco cedo demais: erro de sintaxe e a janela fecha sem avisar nada.
rem Regra: sempre !ARQ! (expansao adiada) e SEMPRE entre aspas.

if not exist ".venv\Scripts\activate" (
  echo Rode o "instalar.bat" primeiro.
  echo.
  pause
  exit /b 1
)
call .venv\Scripts\activate

echo ============================================
echo   Importar dados da planilha
echo ============================================
echo.

rem 1) arquivo arrastado para cima do .bat
if not "%~1"=="" (
  set "ARQ=%~1"
  goto :temarquivo
)

rem 2) procura a planilha mais recente: nesta pasta, Downloads e Area de Trabalho
set "ARQ="
set "BAIXADA="
set "MESA="
for /f "delims=" %%f in ('dir /b /o-d "*.xlsx" 2^>nul') do (
  if not defined ARQ set "ARQ=%%~ff"
)
for /f "delims=" %%f in ('dir /b /o-d "%USERPROFILE%\Downloads\*.xlsx" 2^>nul ^| findstr /i "automacao"') do (
  if not defined BAIXADA set "BAIXADA=%USERPROFILE%\Downloads\%%f"
)
for /f "delims=" %%f in ('dir /b /o-d "%USERPROFILE%\Desktop\*.xlsx" 2^>nul ^| findstr /i "automacao"') do (
  if not defined MESA set "MESA=%USERPROFILE%\Desktop\%%f"
)

echo Planilhas encontradas:
if defined ARQ (
  for %%A in ("!ARQ!") do echo    [1] nesta pasta ......: %%~nxA   ^(modificada em %%~tA^)
)
if defined BAIXADA (
  for %%A in ("!BAIXADA!") do echo    [2] em Downloads .....: %%~nxA   ^(modificada em %%~tA^)
)
if defined MESA (
  for %%A in ("!MESA!") do echo    [3] Area de Trabalho ..: %%~nxA   ^(modificada em %%~tA^)
)
echo    [4] informar outro caminho
echo.
echo    ATENCAO: use a planilha ATUALIZADA, com os dados novos.
echo.
set "OPCAO="
set /p OPCAO="Qual usar? (1/2/3/4): "

if "!OPCAO!"=="2" set "ARQ=!BAIXADA!"
if "!OPCAO!"=="3" set "ARQ=!MESA!"
if "!OPCAO!"=="4" (
  echo.
  set /p ARQ="Arraste o arquivo aqui e tecle Enter: "
)

:temarquivo
rem tira as aspas que vem junto quando o usuario arrasta o arquivo
set "ARQ=!ARQ:"=!"

if "!ARQ!"=="" (
  echo.
  echo Nenhum arquivo escolhido.
  echo.
  pause
  exit /b 1
)
if not exist "!ARQ!" (
  echo.
  echo Arquivo nao encontrado:
  echo    "!ARQ!"
  echo.
  pause
  exit /b 1
)

echo.
echo ============================================
echo   Importando de:
for %%A in ("!ARQ!") do (
  echo   arquivo ....: %%~nxA
  echo   pasta ......: %%~dpA
  echo   modificada .: %%~tA
)
echo ============================================
echo.

echo   O que voce apagou no sistema NAO volta da planilha.
echo   (para trazer tudo de volta assim mesmo, veja o fim desta janela)
echo.

python -m scripts.importar_planilha "!ARQ!"
set "CODIGO=%ERRORLEVEL%"

echo.
echo ============================================
if not "!CODIGO!"=="0" (
  echo   A IMPORTACAO FALHOU  [codigo !CODIGO!]
  echo   Leia a mensagem de erro acima e mande para o TI.
) else (
  echo   Importacao concluida.
  echo   Reinicie o "iniciar.bat" e atualize a pagina com F5.
  echo.
  echo   Precisa recuperar algo que apagou por engano?
  echo     importar.bat  nao faz isso de proposito. Para forcar, rode no
  echo     Prompt de Comando, dentro desta pasta:
  echo        .venv\Scripts\activate
  echo        python -m scripts.importar_planilha "ARQUIVO.xlsx" --refazer
)
echo ============================================
echo.
pause
exit /b !CODIGO!
