from be_utils.utils import get_be_ip, get_rabbitmq_port
from celery import Celery

_celery_client = Celery('celery',
                        broker=f'amqp://{get_be_ip()}:{get_rabbitmq_port()}',
                        BROKER_USER='aim',
                        BROKER_PASSWORD='aim123')


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
