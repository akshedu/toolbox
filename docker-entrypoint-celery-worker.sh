#!/bin/bash
set -e

echo "Apply database migrations"
python manage.py migrate

echo "start celery worker"
celery -A config worker --loglevel=info -f celery.logs
