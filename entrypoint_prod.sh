#!/bin/sh
set -e

# wait for dependent services if necessary (simple sleep for demo)
echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

exec "$@"
