#!/bin/bash
set -e

echo "Apply database migrations"
python manage.py migrate

echo "Schedule scrapers"
python manage.py celery_beat_resource_scraper

echo "start beat service"
celery -A config beat -l info -f celery.logs --scheduler django_celery_beat.schedulers:DatabaseScheduler
