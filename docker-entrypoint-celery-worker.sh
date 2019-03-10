#!/bin/bash
set -e

echo "start celery worker"
celery -A config worker --loglevel=info -f worker.logs
