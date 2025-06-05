#!/bin/sh

set -e  # Exit on any error

echo ""
echo "------------------------------------------"
echo "🚀 Starting container with ROLE=\"$ROLE\""
echo "------------------------------------------"

case "$ROLE" in
  flask)
    echo "🟢 Starting Flask API (Server)..."
    . ~/backend/venv/bin/activate
    exec python app.py
    ;;
    
  slack-celery)
    echo "🔧 Starting Slack Celery worker with tasks concurrently : $CELERY_WORKER"
    . ~/backend/venv/bin/activate
    exec celery -A celery_app.init worker -c $CELERY_WORKER --loglevel=info -Q slack_queue -n data_sources
    ;;

  docs-celery)
    echo "⏰ Starting Docs Celery worker with tasks concurrently : $CELERY_WORKER"
    . ~/backend/venv/bin/activate
    exec celery -A celery_app.init worker -c $CELERY_WORKER --loglevel=info -Q docs_queue -n data_sources
    ;;

  *)
    echo "❌ ERROR: Unknown ROLE \"$ROLE\""
    echo "Valid roles are: flask, slack-celery, doc-celery"
    exit 1
    ;;
esac
