"""
Module for importing non-configured flask extensions
"""
from celery import Celery
from config.configParams import config


def make_celery():
    """Initialize and configure Celery.
    run celery using:
    celery -A celery_app.init worker --loglevel=info
    """
    
    celery_app = Celery(
            'celery_backend',
            broker=f"amqp://rabbitmq:5672",
            BROKER_USER='genie',
            BROKER_PASSWORD='genie123',
            backend="mongodb://mongodb:27017",
            include=['celery_app.tasks']
        )

    celery_app.conf.update(
    task_acks_late=True,  
    task_reject_on_worker_lost=True, 
    timezone='UTC',
    enable_utc=True,
    beat_schedule={
        'fetch-dpr-metrics-every-30-mins': {
            'task': 'celery_app.tasks.fetch_dpr_metrics',
            'schedule': 90.0 # call this function every 15 minutes
        }
    }
)


    return celery_app


celery = make_celery()