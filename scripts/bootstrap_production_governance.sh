#!/usr/bin/env bash
set -euo pipefail
if [[ ! -f .env.production ]]; then echo "Missing .env.production" >&2; exit 1; fi
read -rsp "Temporary Founder Guardian password: " founder_password; echo
if [[ ${#founder_password} -lt 12 ]]; then echo "Use at least 12 characters." >&2; exit 1; fi
docker compose --env-file .env.production -f docker-compose.production.yml exec -T backend \
  python manage.py bootstrap_governance \
  --temporary-password "$founder_password"
echo "Founder Guardian created or updated. Sign in and change the password immediately."
