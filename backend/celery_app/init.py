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
            'schedule': 30.0
        }
    }
)


    return celery_app


celery = make_celery()


# """
# Module for importing non-configured flask extensions
# """
# from celery import Celery
# from prompt_lab.utils.util import get_mongo_url, get_rabbitmq_url


# class CeleryApp:
#     """
#     Singleton class for initializing and configuring Celery.
#     """
#     _instance = None

#     def __new__(cls):
#         if cls._instance is None:
#             cls._instance = super(CeleryApp, cls).__new__(cls)
#             cls._instance._initialize_celery()
#         return cls._instance

#     def _initialize_celery(self):
#         """Initialize the Celery instance."""
#         self.celery_app = Celery(
#             'celery_dpr',
#             broker=get_rabbitmq_url(),
#             BROKER_USER='genie',
#             BROKER_PASSWORD='genie123',
#             backend="rpc://",
#             include=['celery_app.tasks'] 
#         )

#         self.celery_app.conf.update(
#         task_acks_late=True,  
#         task_reject_on_worker_lost=True, 
#         timezone='UTC',
#         enable_utc=True,
#         beat_schedule={
#             'fetch-dpr-metrics-every-30-mins': {
#                 'task': 'celery_app.tasks.fetch_dpr_metrics',
#                 'schedule': 60.0
#             }
#         })


#     @property
#     def app(self):
#         """Get the singleton Celery instance."""
#         return self.celery_app