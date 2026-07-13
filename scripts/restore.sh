#!/usr/bin/env bash
set -euo pipefail
if [[ $# -ne 1 ]]; then
  echo "Usage: ./scripts/restore.sh backups/ecorevive-TIMESTAMP.sql.gz" >&2
  exit 1
fi
if [[ ! -f .env.production ]]; then echo "Missing .env.production" >&2; exit 1; fi
backup="$1"
if [[ ! -f "$backup" ]]; then echo "Backup not found: $backup" >&2; exit 1; fi
read -rp "This replaces the production database. Type RESTORE to continue: " answer
if [[ "$answer" != "RESTORE" ]]; then echo "Cancelled."; exit 1; fi
gzip -dc "$backup" | docker compose --env-file .env.production -f docker-compose.production.yml exec -T db \
  sh -c 'psql -U "$POSTGRES_USER" "$POSTGRES_DB"'
echo "Restore completed. Run application checks before reopening operations."
