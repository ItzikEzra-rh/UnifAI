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
    
    host = config.get("dpr", "rabbitmq_host")
    port = config.get("dpr", "rabbitmq_port")
    
    celery_app = Celery('celery_reviewer',
                        broker=host.format(port=port),
                        # broker="pyamqp://guest:guest@localhost//",
                        backend="rpc://",
                        include=['celery_app.tasks'])  

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