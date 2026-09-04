#!/bin/bash
# Prepara um servidor Ubuntu novo para rodar o ATS.
# Uso:  bash deploy.sh
set -e

echo "============================================"
echo "  ATS TLM — preparando o servidor"
echo "============================================"

if [ "$EUID" -ne 0 ]; then echo "Rode como root (ou com sudo)."; exit 1; fi

echo "-> Atualizando o sistema..."
apt-get update -qq && apt-get upgrade -y -qq

echo "-> Instalando o Docker..."
if ! command -v docker >/dev/null 2>&1; then
  curl -fsSL https://get.docker.com | sh
fi

echo "-> Ajustando o firewall (libera apenas 22, 80 e 443)..."
apt-get install -y -qq ufw
ufw allow 22/tcp  >/dev/null
ufw allow 80/tcp  >/dev/null
ufw allow 443/tcp >/dev/null
ufw --force enable >/dev/null

echo "-> Verificando a configuracao..."
if [ ! -f .env ]; then
  cp .env.exemplo .env
  # gera senha e chave fortes automaticamente
  SENHA=$(openssl rand -base64 24 | tr -d '/+=' | head -c 28)
  CHAVE=$(openssl rand -base64 48)
  sed -i "s|^POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=$SENHA|" .env
  sed -i "s|^SECRET_KEY=.*|SECRET_KEY=$CHAVE|" .env
  echo
  echo "   Criei o arquivo .env com senha e chave geradas."
  echo "   AGORA preencha o DOMINIO e o EMAIL_ADMIN:"
  echo "     nano .env"
  echo "   Depois rode este script de novo."
  exit 0
fi

if grep -q "suaempresa.com.br" .env; then
  echo "   Falta preencher DOMINIO e EMAIL_ADMIN no arquivo .env."
  echo "     nano .env"
  exit 1
fi

echo "-> Subindo o sistema..."
docker compose up -d --build

echo "-> Agendando o backup diario (2h da manha)..."
chmod +x backup_postgres.sh
CAMINHO=$(pwd)
( crontab -l 2>/dev/null | grep -v backup_postgres.sh ; echo "0 2 * * * $CAMINHO/backup_postgres.sh" ) | crontab -

DOM=$(grep ^DOMINIO= .env | cut -d= -f2)
echo
echo "============================================"
echo "  Pronto!"
echo
echo "  Acesse:  https://$DOM"
echo "  (o certificado HTTPS leva ~1 minuto na primeira vez)"
echo
echo "  Proximo passo — criar o primeiro usuario:"
echo "    docker compose exec sistema python -m scripts.criar_admin \\"
echo "      \"Hiago TI\" ti@tlmequipamentos.com.br SuaSenhaForte TI"
echo
echo "  Para trazer os dados atuais, envie o rh_ats.db para esta pasta e rode:"
echo "    docker compose exec sistema python -m scripts.migrar_para_postgres"
echo "============================================"
