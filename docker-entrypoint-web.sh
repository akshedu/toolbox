#!/bin/bash
set -e

echo "Apply database migrations"
python manage.py migrate

echo "Schedule scrapers"
python manage.py celery_beat_resource_scraper &
python manage.py celery_beat_top_videos

echo "Starting gunicorn"
gunicorn config.wsgi:application --certfile keys/cert.pem \
    --keyfile keys/key.pem --bind 0.0.0.0:8000 --workers 4 \
    --timeout 308000
