"""
Module for importing non-configured flask extensions
"""
from celery import Celery
from utils.util import get_mongo_url, get_rabbitmq_url


class CeleryApp:
    """
    Singleton class for initializing and configuring Celery.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CeleryApp, cls).__new__(cls)
            cls._instance._initialize_celery()
        return cls._instance

    def _initialize_celery(self):
        """Initialize the Celery instance."""
        self.celery_app = Celery(
            'celery_promp_lab',
            broker=get_rabbitmq_url(),
            BROKER_USER='genie',
            BROKER_PASSWORD='genie123',
            backend=get_mongo_url(),
            include=['celery_app.tasks']
        )

    @property
    def app(self):
        """Get the singleton Celery instance."""
        return self.celery_app
