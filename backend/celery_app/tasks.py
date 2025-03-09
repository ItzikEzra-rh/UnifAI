import logging
from celery_batches import Batches
from providers.dpr import celery_fetch_dpr
from celery_app.init import celery

import traceback
import asyncio

@celery.task(bind=True, max_retries=16, default_retry_delay=30)
def fetch_dpr_metrics(self):
    try:
        asyncio.run(celery_fetch_dpr())
    except Exception as e:
        print(f"fetch_dpr_metrics task failed: {e}. Retrying...")
        raise self.retry(exc=e)