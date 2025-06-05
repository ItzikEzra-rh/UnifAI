import os
from global_utils.celery_app import CeleryApp
from global_utils.config import ConfigManager

initial_config = {
  "rabbitmq_port": "5672",
  "rabbitmq_ip": "0.0.0.0",
  "mongodb_port": "27017",
  "mongodb_ip": "0.0.0.0"
}

config = (
    ConfigManager()
    if os.getenv("BACKEND_ENV") == "production"
    else ConfigManager(initial_config=initial_config)
)

celery = CeleryApp(
    broker_user_name="genie", 
    broker_password="genie123", 
    task_modules=[
            "data_sources.slack.slack_tasks", 
            "data_sources.docs.docs_tasks"
            ]
          ).app

# TODO: In order to start celery worker, below line should be triggered from backend/
# celery -A celery_app.init worker -c 1 --loglevel=info -Q slack_queue -n data_sources
# celery -A celery_app.init worker -c 1 --loglevel=info -Q docs_queue -n data_sources