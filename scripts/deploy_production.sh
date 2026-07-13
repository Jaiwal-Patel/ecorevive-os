#!/usr/bin/env bash
set -euo pipefail
if [[ ! -f .env.production ]]; then
  echo "Missing .env.production. Copy .env.production.example and replace every placeholder." >&2
  exit 1
fi
if grep -Eq 'GENERATE_|YOUR_DOMAIN|smtp\.example' .env.production; then
  echo "Production placeholders remain in .env.production." >&2
  exit 1
fi
docker compose --env-file .env.production -f docker-compose.production.yml pull
docker compose --env-file .env.production -f docker-compose.production.yml up -d --build
docker compose --env-file .env.production -f docker-compose.production.yml exec -T backend python manage.py check --deploy
echo "Deployment complete. Review logs with: docker compose --env-file .env.production -f docker-compose.production.yml logs -f"
