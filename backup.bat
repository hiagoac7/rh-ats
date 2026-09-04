@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================
echo   Backup do banco de dados
echo ============================================
echo.
if not exist "rh_ats.db" (
  echo Banco nao encontrado nesta pasta.
  pause
  exit /b
)
if not exist "backups" mkdir backups
set DATA=%date:~6,4%-%date:~3,2%-%date:~0,2%
set HORA=%time:~0,2%%time:~3,2%
set HORA=%HORA: =0%
copy /Y "rh_ats.db" "backups\rh_ats_%DATA%_%HORA%.db" >nul
if %errorlevel%==0 (
  echo   Backup salvo em: backups\rh_ats_%DATA%_%HORA%.db
  echo.
  echo   Backups existentes:
  dir /b /o-d backups\*.db
) else (
  echo   *** Falha ao copiar. Feche o sistema (iniciar.bat) e tente de novo. ***
)
echo.
pause
