#!/usr/bin/env bash
set -euo pipefail

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "Created .env from .env.example"
fi

FOUNDER_EMAIL_VALUE="$(awk -F= '$1=="FOUNDER_EMAIL"{print substr($0,index($0,"=")+1)}' .env | tail -1)"
FOUNDER_NAME_VALUE="$(awk -F= '$1=="FOUNDER_FULL_NAME"{print substr($0,index($0,"=")+1)}' .env | tail -1)"
FOUNDER_EMAIL_VALUE="${FOUNDER_EMAIL_VALUE:-ujaiwal@outlook.com}"
FOUNDER_NAME_VALUE="${FOUNDER_NAME_VALUE:-Jaiwal Patel}"
TEMP_PASSWORD="EcoRevive-$(date +%s)-ChangeMe!"

docker compose build
docker compose up -d db redis
docker compose run --rm backend python manage.py migrate --noinput
docker compose run --rm backend python manage.py seed_ecorevive
docker compose run --rm backend python manage.py bootstrap_governance \
  --founder-email "$FOUNDER_EMAIL_VALUE" \
  --founder-name "$FOUNDER_NAME_VALUE" \
  --temporary-password "$TEMP_PASSWORD"
docker compose up -d backend worker frontend
docker compose exec -T backend python manage.py check

printf '\nEcoRevive OS is ready.\n'
printf 'Frontend: open forwarded port 5173\n'
printf 'API docs: open forwarded port 8000 and add /api/docs/\n'
printf 'Founder email: %s\n' "$FOUNDER_EMAIL_VALUE"
printf 'Temporary password: %s\n' "$TEMP_PASSWORD"
printf '\nChange the temporary password immediately under Account.\n'
printf 'Create Founder Recovery later using a separate secured email and the documented governance procedure.\n'
