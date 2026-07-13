#!/usr/bin/env bash
set -euo pipefail
python - <<'PY'
import secrets
print(f"DJANGO_SECRET_KEY={secrets.token_urlsafe(64)}")
print(f"POSTGRES_PASSWORD={secrets.token_urlsafe(32)}")
print(f"REDIS_PASSWORD={secrets.token_urlsafe(32)}")
PY
