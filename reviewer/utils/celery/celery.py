from utils.util import get_rabbitmq_url
from celery import Celery

_celery_client = Celery('celery',
                        broker=get_rabbitmq_url(),
                        BROKER_USER='genie',
                        BROKER_PASSWORD='genie123')


def celery_client():
    """
    get the db instance
    """
    global _celery_client
    return _celery_client


def send_task(task_name, data, celery_queue):
    client = celery_client()
    client.send_task(f"celery_app.tasks.{task_name}",
                     kwargs=data,
                     queue=celery_queue)
