#!/bin/bash

envsubst < config/config.json > config/config.tmp && mv config/config.tmp config/config.json

case "$1" in
  "reviewer")
    celery -A celery_app.init worker -c 1 --loglevel=info -Q reviewer_queue -n reviewer
    ;;
  "reviewer_pass_fail")
    celery -A celery_app.init worker -c 1 --loglevel=info -Q reviewer_pass_queue,reviewer_fail_queue -n reviewer
    ;;
  "bash")
    bash
    ;;
  *)
    echo "Please specify service: reviewer, or reviewer_pass_fail"
    exit 1
    ;;
esac
