#!/usr/bin/env bash
set -euo pipefail

if ! command -v docker >/dev/null 2>&1; then
  echo "ERROR: Docker is not installed in this environment." >&2
  echo "In GitHub Codespaces, rebuild the devcontainer and verify 'docker info' succeeds." >&2
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "ERROR: Docker is installed, but the Docker daemon is not ready." >&2
  echo "Run 'docker info' for details, then retry." >&2
  exit 1
fi

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "Created .env from .env.example"
fi

FOUNDER_EMAIL_VALUE="$(awk -F= '$1=="FOUNDER_EMAIL"{print substr($0,index($0,"=")+1)}' .env | tail -1)"
FOUNDER_NAME_VALUE="$(awk -F= '$1=="FOUNDER_FULL_NAME"{print substr($0,index($0,"=")+1)}' .env | tail -1)"
FOUNDER_EMAIL_VALUE="${FOUNDER_EMAIL_VALUE:-ujaiwal@outlook.com}"
FOUNDER_NAME_VALUE="${FOUNDER_NAME_VALUE:-Jaiwal Patel}"
TEMP_PASSWORD="EcoRevive-$(date +%s)-ChangeMe!"

printf '\n[1/7] Building backend image...\n'
BUILDKIT_PROGRESS=plain docker compose build backend

printf '\n[2/7] Building frontend image...\n'
BUILDKIT_PROGRESS=plain docker compose build frontend

printf '\n[3/7] Starting PostgreSQL and Redis...\n'
docker compose up -d db redis

printf '\n[4/7] Applying database migrations...\n'
docker compose run --rm backend python manage.py migrate --noinput

printf '\n[5/7] Seeding EcoRevive reference data...\n'
docker compose run --rm backend python manage.py seed_ecorevive

printf '\n[6/7] Creating or updating Founder Guardian...\n'
docker compose run --rm backend python manage.py bootstrap_governance \
  --founder-email "$FOUNDER_EMAIL_VALUE" \
  --founder-name "$FOUNDER_NAME_VALUE" \
  --temporary-password "$TEMP_PASSWORD"

printf '\n[7/7] Starting EcoRevive services...\n'
docker compose up -d backend worker frontend
docker compose exec -T backend python manage.py check

printf '\nEcoRevive OS is ready.\n'
printf 'Frontend: open forwarded port 5173\n'
printf 'API docs: open forwarded port 8000 and add /api/docs/\n'
printf 'Founder email: %s\n' "$FOUNDER_EMAIL_VALUE"
printf 'Temporary password: %s\n' "$TEMP_PASSWORD"
printf '\nChange the temporary password immediately under Account.\n'
printf 'Create Founder Recovery later using a separate secured email and the documented governance procedure.\n'
