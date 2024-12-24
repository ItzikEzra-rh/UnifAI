#!/bin/bash

envsubst < config/config.json > config/config.tmp && mv config/config.tmp config/config.json

case "$1" in
  "prompt_processor")
    celery -A celery_app.init worker -c 3 --prefetch-multiplier 1 --loglevel=info -Q prompts_process_queue -n prompts_process_queue
    ;;
  "prompt_dispatcher")
    celery -A celery_app.init worker -c 1 --loglevel=info -Q reviewer_passed -n reviewer_passed
    ;;
  "prompt_submiter")
    python3 main.py
    ;;
  "bash")
    bash
    ;;
  *)
    echo "Please specify service: prompt_processor, prompt_submiter or prompt_dispatcher"
    exit 1
    ;;
esac