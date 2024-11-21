import logging
from celery_batches import Batches
from celery_app.init import celery

from utils.celery.celery import send_task
import traceback


# @celery.on_after_configure.connect
# def setup_periodic_tasks(sender, **kwargs):
#     task_name = 'Periodic job - kill live samples once mongo cross storage limitation'
#     sender.add_periodic_task(60.0, mongo_storage_limitation_task.s(), name=task_name)


@celery.task()
def fetch_resources_task():
    pass


# send_task(task_name="notify_statistics_master_worker",
#           data=dict(sample_id=sample_id,
#                     worker_id=sample.current_worker_id),
#           celery_queue='asc_statistics')

@celery.task(base=Batches, flush_every=10, flush_interval=1)
def samples_handler(requests):
    live_samples = []
    for request in requests:
        raw_sample_1 = request.kwargs['raw_sample_1']
        raw_sample_2 = request.kwargs['raw_sample_2']
