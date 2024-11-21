import logging
from celery_batches import Batches
from celery_app.init import celery
from g_eval.g_eval_review import process_elements, save_elements

from utils.celery.celery import send_task
import traceback


# @celery.on_after_configure.connect
# def setup_periodic_tasks(sender, **kwargs):
#     task_name = 'Periodic job - kill live samples once mongo cross storage limitation'
#     sender.add_periodic_task(60.0, mongo_storage_limitation_task.s(), name=task_name)

# @celery.task(base=Batches, flush_every=10, flush_interval=1)
# def samples_handler(requests):
#     live_samples = []
#     for request in requests:
#         raw_sample_1 = request.kwargs['raw_sample_1']
#         raw_sample_2 = request.kwargs['raw_sample_2']

@celery.task()
def fetch_prompt_lab_generated_objects(data):
    process_elements(data)

@celery.task()
def fetch_reviewer_passed_generated_objects(data):
    save_elements(data)

@celery.task()
def fetch_reviewer_failed_generated_objects(data):
    pass