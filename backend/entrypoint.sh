#!/bin/sh

# Exit immediately if a command exits with a non-zero status
set -e

# 1. Wait for MySQL (with Timeout)
echo "Waiting for MySQL at $DB_HOST:$DB_PORT..."

# Set default values if not set
DB_HOST=${DB_HOST:-db}
DB_PORT=${DB_PORT:-3306}

timeout=30
while ! nc -z $DB_HOST $DB_PORT; do
  timeout=$((timeout-1))
  if [ $timeout -eq 0 ]; then
    echo "Error: Timed out waiting for MySQL at $DB_HOST:$DB_PORT"
    exit 1
  fi
  sleep 1
done
echo "MySQL started"

# 2. Run Migrations (Conditional)
if [ "$RUN_MIGRATIONS" = "true" ]; then
    echo "Running migrations..."
    python manage.py migrate
fi

# 3. Collect Static Files (Conditional)
if [ "$RUN_COLLECTSTATIC" = "true" ]; then
    echo "Collecting static files..."
    python manage.py collectstatic --noinput
fi

# 4. Run Gunicorn
echo "Starting Gunicorn..."
exec "$@"
 