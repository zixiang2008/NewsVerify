#!/usr/bin/env bash
set -euo pipefail
TS=$(date +%Y%m%d-%H%M%S)
OUT="/backups/newsverify-${TS}.sql.gz"
mkdir -p /backups
docker compose exec -T db pg_dump -U "${POSTGRES_USER:-newsverify}" "${POSTGRES_DB:-newsverify}" | gzip > "$OUT"
echo "Backup written to $OUT"