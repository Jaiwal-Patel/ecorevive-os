#!/usr/bin/env sh
set -eu
python manage.py migrate --noinput
python manage.py collectstatic --noinput
python manage.py seed_ecorevive
exec gunicorn ecorevive.wsgi:application --bind 0.0.0.0:8000 --workers "${GUNICORN_WORKERS:-3}" --timeout 90 --access-logfile - --error-logfile -
