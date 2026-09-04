#!/bin/sh
# Backup diario do banco. Coloque no cron:
#   0 2 * * * /caminho/rh_ats/backup_postgres.sh
cd "$(dirname "$0")" || exit 1
DATA=$(date +%Y-%m-%d_%H%M)
mkdir -p backups
docker compose exec -T banco pg_dump -U ats --clean --if-exists rh_ats | gzip > "backups/rh_ats_$DATA.sql.gz"
# mantem os ultimos 30 dias
find backups -name "rh_ats_*.sql.gz" -mtime +30 -delete
echo "Backup salvo: backups/rh_ats_$DATA.sql.gz"
