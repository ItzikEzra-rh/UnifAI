"""
Module for importing non-configured flask extensions
"""
from celery import Celery
from config.configParams import config_params


def make_celery():
    """Initialize and configure Celery.
    run celery using:
    celery -A celery_app.init worker --loglevel=info
    """
    celery_app = Celery('celery_promp_lab',
                        broker=config_params.RABBITMQ_URL,
                        backend='mongodb://your-mongodb-url/your-collection',
                        include=['celery_app.tasks'])
    return celery_app


celery = make_celery()
