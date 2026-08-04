#!/usr/bin/env bash
set -Eeuo pipefail

ENV_FILE=".env.azure"
COMPOSE_FILE="docker-compose.azure.yml"
MEDIA_DIR="/var/lib/ecorevive/media"

compose() {
  docker compose \
    --env-file "${ENV_FILE}" \
    -f "${COMPOSE_FILE}" \
    "$@"
}

fail() {
  echo "ERROR: $*" >&2
  exit 1
}

on_error() {
  local exit_code=$?

  echo
  echo "Azure deployment failed with exit code ${exit_code}." >&2
  echo "Recent service status:" >&2

  compose ps >&2 || true

  echo
  echo "Recent backend and worker logs:" >&2

  compose logs \
    --tail=100 \
    backend \
    worker >&2 || true

  exit "${exit_code}"
}

trap on_error ERR

if [[ ! -f "${ENV_FILE}" ]]; then
  fail \
    "Missing ${ENV_FILE}. Copy .env.azure.example to " \
    "${ENV_FILE} and replace every placeholder."
fi

if [[ ! -f "${COMPOSE_FILE}" ]]; then
  fail "Missing ${COMPOSE_FILE}."
fi

if grep -Eq \
  '^[[:space:]]*[A-Za-z_][A-Za-z0-9_]*=.*(CHANGE_ME|YOUR_AZURE|YOUR_STATIC|YOUR_)' \
  "${ENV_FILE}"; then
  fail \
    "Azure placeholders remain in ${ENV_FILE}. " \
    "Replace them before deployment."
fi

if ! command -v docker >/dev/null 2>&1; then
  fail "Docker is not installed."
fi

if ! docker compose version >/dev/null 2>&1; then
  fail "The Docker Compose plugin is not installed."
fi

if ! docker info >/dev/null 2>&1; then
  fail \
    "Docker is not available to the current user. " \
    "Check the Docker service and user permissions."
fi

file_mode="$(
  stat -c '%a' "${ENV_FILE}" 2>/dev/null \
    || stat -f '%Lp' "${ENV_FILE}"
)"

if [[ "${file_mode}" != "600" ]]; then
  echo \
    "Securing ${ENV_FILE} permissions " \
    "(previous mode: ${file_mode})."

  chmod 600 "${ENV_FILE}"
fi

echo "Validating Azure Compose configuration..."
compose config --quiet

echo "Preparing persistent media directory..."

if [[ -d "${MEDIA_DIR}" ]]; then
  if [[ ! -w "${MEDIA_DIR}" ]]; then
    sudo chown -R \
      "$(id -u):$(id -g)" \
      "${MEDIA_DIR}"
  fi
else
  sudo install \
    -d \
    -m 0750 \
    -o "$(id -u)" \
    -g "$(id -g)" \
    "${MEDIA_DIR}"
fi

echo "Pulling current Redis and Caddy images..."
compose pull redis caddy

echo "Building the EcoRevive backend image..."
compose build backend worker

echo "Starting Redis..."
compose up -d redis

echo "Starting Django..."
compose up -d backend

backend_container="$(
  compose ps -q backend
)"

if [[ -z "${backend_container}" ]]; then
  fail "The backend container was not created."
fi

echo "Waiting for Django to become healthy..."

for attempt in $(seq 1 30); do
  backend_health="$(
    docker inspect \
      --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' \
      "${backend_container}"
  )"

  if [[ "${backend_health}" == "healthy" ]]; then
    echo "Django is healthy."
    break
  fi

  if [[ "${backend_health}" == "unhealthy" ]]; then
    compose logs --tail=100 backend
    fail "Django became unhealthy."
  fi

  if [[ "${attempt}" -eq 30 ]]; then
    compose logs --tail=100 backend
    fail "Django did not become healthy in time."
  fi

  sleep 5
done

echo "Running Django production checks..."
compose exec -T backend \
  python manage.py check --deploy

echo "Checking for unapplied migrations..."
compose exec -T backend \
  python manage.py migrate --check

echo "Starting Celery and Caddy..."
compose up -d worker caddy

echo "Waiting briefly for service startup..."
sleep 8

echo
echo "Service status:"
compose ps

echo
echo "Registered Celery tasks:"
compose exec -T worker \
  celery -A ecorevive inspect registered \
  --timeout=10 || {
    echo \
      "WARNING: Celery task inspection did not respond. " \
      "Review the worker logs."
  }

domain="$(
  awk -F= '
    $1 == "ECOREVIVE_DOMAIN" {
      sub(/^[^=]*=/, "")
      print
      exit
    }
  ' "${ENV_FILE}"
)"

echo
echo "Azure deployment completed."
echo
echo "Backend URL:"
echo "  https://${domain}"
echo
echo "Useful commands:"
echo
echo "  ./scripts/deploy_azure.sh"
echo
echo "  docker compose --env-file .env.azure \\"
echo "    -f docker-compose.azure.yml ps"
echo
echo "  docker compose --env-file .env.azure \\"
echo "    -f docker-compose.azure.yml logs -f backend worker caddy"
