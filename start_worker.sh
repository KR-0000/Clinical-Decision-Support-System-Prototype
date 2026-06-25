#!/bin/sh
# start_worker.sh
# Runs alongside Celery on Render's free web service tier.
# Render requires a process to bind a port — this script starts a minimal
# health server in the background, then runs Celery in the foreground.
# When Celery exits (crash or restart), the container exits correctly.

echo "Starting health server on port ${PORT:-8001}..."
python worker_health.py &

echo "Starting Celery worker..."
exec celery -A app.workers.tasks worker --loglevel=info --concurrency=1