#!/bin/sh
set -e

echo "DJANGO_ENV=$DJANGO_ENV"

echo "Running collectstatic..."
python manage.py collectstatic --noinput

echo "Starting gunicorn..."
exec "$@"
