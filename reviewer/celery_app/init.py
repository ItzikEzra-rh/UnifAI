"""
Module for importing non-configured flask extensions
"""
from celery import Celery
from utils.util import get_mongo_url, get_rabbitmq_url


def make_celery():
    """Initialize and configure Celery.
    run celery using:
    celery -A celery_app.init worker --loglevel=info
    """
    celery_app = Celery('celery_reviewer',
                        broker=get_rabbitmq_url(),
                        BROKER_USER='genie',
                        BROKER_PASSWORD='genie123',
                        backend=get_mongo_url(),
                        include=['celery_app.tasks'])
    return celery_app


celery = make_celery()
