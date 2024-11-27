import logging
from celery_batches import Batches
from celery_app.init import celery
from g_eval.review import process_elements, save_elements

from utils.celery.celery import send_task
import traceback
import asyncio

@celery.task()
def fetch_prompt_lab_generated_objects(data):
    asyncio.run(process_elements(data))

@celery.task()
def fetch_reviewer_passed_generated_objects(data):
    save_elements(data)

@celery.task()
def fetch_reviewer_failed_generated_objects(data):
    pass