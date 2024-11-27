from utils.util import get_rabbitmq_url
from celery_app.init import celery


def send_task(task_name, celery_queue, **kwargs):
    celery.send_task(f"celery_app.tasks.{task_name}",
                     queue=celery_queue,
                     kwargs=kwargs)
