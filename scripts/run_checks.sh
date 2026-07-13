#!/usr/bin/env bash
set -euo pipefail

docker compose exec -T backend python manage.py check
docker compose exec -T backend python manage.py makemigrations --check --dry-run
docker compose exec -T backend ruff check .
docker compose exec -T backend pytest
docker compose exec -T frontend npm run lint
docker compose exec -T frontend npm run test -- --run
docker compose exec -T frontend npm run build
docker compose exec -T backend python manage.py collectstatic --noinput

echo "All checks passed."
