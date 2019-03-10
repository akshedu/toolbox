#!/bin/bash
set -e

echo "start beat service"
celery -A config beat -l info -f beat.logs --scheduler django_celery_beat.schedulers:DatabaseScheduler
