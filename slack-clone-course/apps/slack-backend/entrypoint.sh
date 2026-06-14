#!/usr/bin/env bash
# One entrypoint, several roles. The first argument selects what this container does,
# so the same image runs the web server, the Celery worker, and Beat.
set -euo pipefail

role="${1:-web}"

case "$role" in
  web)
    # Migrations are normally run by a dedicated Job in Kubernetes (Module 13). For
    # local compose convenience, run them here when RUN_MIGRATIONS=1.
    if [ "${RUN_MIGRATIONS:-0}" = "1" ]; then
      python manage.py migrate --noinput
      python manage.py collectstatic --noinput
    fi
    # Serve HTTP + WebSockets over ASGI. For multiple processes behind one container
    # use gunicorn: gunicorn config.asgi:application -k uvicorn.workers.UvicornWorker -w 3
    exec uvicorn config.asgi:application --host 0.0.0.0 --port 8000
    ;;
  worker)
    exec celery -A config worker -l info --concurrency "${CELERY_CONCURRENCY:-4}"
    ;;
  beat)
    exec celery -A config beat -l info
    ;;
  migrate)
    python manage.py migrate --noinput
    python manage.py collectstatic --noinput
    ;;
  *)
    echo "Unknown role: $role (expected web|worker|beat|migrate)"; exit 1
    ;;
esac
