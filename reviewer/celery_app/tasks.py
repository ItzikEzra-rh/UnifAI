import logging
from celery_batches import Batches
from celery_app.init import celery
from g_eval.review import process_elements, save_elements

from utils.celery.celery import send_task
import traceback
import asyncio


@celery.task(bind=True, max_retries=16, default_retry_delay=30)  # 8 minutes
def fetch_prompt_lab_generated_objects(self, batch):
    try:
        asyncio.run(process_elements(batch))
    except Exception as e:
        # Log the exception and retry the task
        print(f"fetch_prompt_lab_generated_objects task failed: {e}. Retrying...")
        raise self.retry(exc=e)
