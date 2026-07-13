#!/usr/bin/env bash
set -euo pipefail
if [[ ! -f .env.production ]]; then echo "Missing .env.production" >&2; exit 1; fi
mkdir -p backups
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
docker compose --env-file .env.production -f docker-compose.production.yml exec -T db \
  sh -c 'pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"' | gzip > "backups/ecorevive-${stamp}.sql.gz"
echo "Created backups/ecorevive-${stamp}.sql.gz"
