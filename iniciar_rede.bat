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
echo   Sistema disponivel para a REDE da empresa
echo ============================================
echo.
echo   Neste computador ...: http://localhost:8000
echo.
echo   Os outros devem acessar por um destes enderecos:
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
  for /f "tokens=* delims= " %%b in ("%%a") do echo        http://%%b:8000
)
echo.
echo   Se nao abrir na outra maquina, libere a porta 8000 no Firewall
echo   (execute uma vez o "liberar_firewall.bat" como administrador).
echo.
echo   Para desligar: feche esta janela ou aperte Ctrl+C
echo ============================================
echo.
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
pause
