#!/bin/sh
set -e

echo "DJANGO_ENV=$DJANGO_ENV"

if [ "$DJANGO_ENV" = "prod" ]; then
    echo "Waiting for PostgreSQL..."
    attempts=0
    until pg_isready \
        --host="$PROD_DB_HOST" \
        --port="${PROD_DB_PORT:-5432}" \
        --dbname="$PROD_DB_NAME" \
        --username="$PROD_DB_USER" \
        --quiet
    do
        attempts=$((attempts + 1))
        if [ "$attempts" -ge 30 ]; then
            echo "PostgreSQL is unavailable after 60 seconds; aborting startup." >&2
            exit 1
        fi
        sleep 2
    done
    echo "PostgreSQL is ready."
fi

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting feedback notification worker..."
python manage.py run_feedback_worker --interval 60 &

echo "Starting gunicorn..."
exec "$@"
