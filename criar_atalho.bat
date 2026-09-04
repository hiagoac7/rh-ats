@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Instalar o ATS neste notebook
echo ============================================
echo   ATS TLM — criar atalho neste computador
echo ============================================
echo.
echo Informe o endereco do sistema.
echo   Exemplos:
echo     https://ats.tlmequipamentos.com.br
echo     http://192.168.0.10:8000     (servidor na rede da empresa)
echo.
set /p ENDERECO="Endereco: "
if "%ENDERECO%"=="" (
  echo Endereco vazio. Cancelado.
  pause
  exit /b
)

rem escolhe o navegador disponivel
set NAV=
if exist "%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe" set NAV=%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe
if exist "%ProgramFiles%\Microsoft\Edge\Application\msedge.exe" set NAV=%ProgramFiles%\Microsoft\Edge\Application\msedge.exe
if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" set NAV=%ProgramFiles%\Google\Chrome\Application\chrome.exe
if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" set NAV=%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe
if "%NAV%"=="" (
  echo Nao encontrei o Edge nem o Chrome neste computador.
  pause
  exit /b
)

rem copia o icone para um lugar fixo
if not exist "%LOCALAPPDATA%\ATS-TLM" mkdir "%LOCALAPPDATA%\ATS-TLM"
if exist "ats.ico" copy /Y "ats.ico" "%LOCALAPPDATA%\ATS-TLM\ats.ico" >nul

rem cria o atalho na area de trabalho, abrindo em janela propria (--app)
powershell -NoProfile -Command ^
  "$w=New-Object -ComObject WScript.Shell; ^
   $a=$w.CreateShortcut([Environment]::GetFolderPath('Desktop')+'\ATS - Recrutamento.lnk'); ^
   $a.TargetPath='%NAV%'; ^
   $a.Arguments='--app=%ENDERECO%'; ^
   $a.IconLocation='%LOCALAPPDATA%\ATS-TLM\ats.ico'; ^
   $a.Description='Sistema de Recrutamento e Selecao — TLM'; ^
   $a.Save()"

echo.
echo ============================================
echo   Pronto! O atalho "ATS - Recrutamento"
echo   esta na Area de Trabalho.
echo.
echo   Ele abre em janela propria, sem barra de
echo   navegador — com cara de aplicativo.
echo ============================================
echo.
pause
