#!/usr/bin/env sh
set -eu

python manage.py migrate --noinput
python manage.py collectstatic --noinput

if [ "${DJANGO_DEBUG:-false}" = "true" ]; then
  exec python manage.py runserver 0.0.0.0:8000
fi

exec gunicorn ecorevive.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 120
