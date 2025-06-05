#!/bin/sh

set -e  # Exit on any error

echo ""
echo "------------------------------------------"
echo "🚀 Starting container with ROLE=\"$ROLE\""
echo "------------------------------------------"

case "$ROLE" in
  flask)
    echo "🟢 Starting Flask API (Server)..."
    exec . ~/backend/venv/bin/activate && python app.py
    ;;
    
  slack-celery)
    echo "🔧 Starting Slack Celery worker..."
   exec . ~/backend/venv/bin/activate  && celery -A celery_app.init worker -c 1 --loglevel=info -Q slack_queue -n data_sources
    ;;

  doc-celery)
    echo "⏰ Starting Docs Celery worker..."
    exec . ~/backend/venv/bin/activate  && celery -A celery_app.init worker -c 1 --loglevel=info -Q docs_queue -n data_sources
    ;;

  *)
    echo "❌ ERROR: Unknown ROLE \"$ROLE\""
    echo "Valid roles are: flask, slack-celery, doc-celery"
    exit 1
    ;;
esac