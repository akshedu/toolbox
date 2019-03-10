#!/bin/bash
set -e

echo "Apply database migrations"
python manage.py migrate

echo "Schedule scrapers"
python manage.py celery_beat_resource_scraper &
python manage.py celery_beat_top_videos

echo "runserver"
python manage.py runserver 0.0.0.0:8000
