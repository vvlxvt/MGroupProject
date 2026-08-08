#!/bin/sh
set -e

echo "DJANGO_ENV=$DJANGO_ENV"

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting feedback notification worker..."
python manage.py run_feedback_worker --interval 60 &

echo "Starting gunicorn..."
exec "$@"
