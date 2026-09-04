@echo off
chcp 65001 >nul
net session >nul 2>&1
if %errorlevel% neq 0 (
  echo Clique com o botao direito neste arquivo e escolha
  echo "Executar como administrador".
  pause
  exit /b
)
netsh advfirewall firewall delete rule name="ATS TLM (porta 8000)" >nul 2>&1
netsh advfirewall firewall add rule name="ATS TLM (porta 8000)" dir=in action=allow protocol=TCP localport=8000
echo.
echo Porta 8000 liberada no Firewall do Windows.
echo Agora os outros computadores da rede conseguem acessar o sistema.
echo.
pause
