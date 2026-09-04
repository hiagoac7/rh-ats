#!/bin/sh
# Restaura o banco a partir de um backup.
#
# Uso:   ./restaurar_backup.sh backups/rh_ats_2026-08-03_0200.sql.gz
#
# ATENCAO: isto SUBSTITUI os dados atuais pelos do backup.
# Um backup do estado atual e gerado antes, por seguranca.
set -e
cd "$(dirname "$0")" || exit 1

ARQ="$1"
if [ -z "$ARQ" ] || [ ! -f "$ARQ" ]; then
  echo "Informe o arquivo de backup. Disponiveis:"
  ls -1t backups/*.sql.gz 2>/dev/null | head -10
  exit 1
fi

echo "Isto vai SUBSTITUIR os dados atuais pelos de:"
echo "   $ARQ"
printf "Digite CONFIRMAR para continuar: "
read RESP
[ "$RESP" = "CONFIRMAR" ] || { echo "Cancelado."; exit 1; }

echo "-> Guardando o estado atual antes de mexer..."
mkdir -p backups
docker compose exec -T banco pg_dump -U ats rh_ats | gzip > "backups/antes_da_restauracao_$(date +%Y-%m-%d_%H%M).sql.gz"

echo "-> Restaurando..."
docker compose stop sistema
gunzip -c "$ARQ" | docker compose exec -T banco psql -U ats -d rh_ats
docker compose start sistema

echo
echo "Pronto. Confira o sistema no navegador."
echo "Se algo estiver errado, o estado anterior esta em backups/antes_da_restauracao_*.sql.gz"
