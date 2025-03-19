import logging
from backend.celery_app.init import CeleryApp
from providers.dpr import celery_fetch_dpr

@CeleryApp().app.task(bind=True, max_retries=16, default_retry_delay=30)  # 8 minutes till fail
def fetch_dpr_metrics(self, batch):
    """
    Celery task for the metrics fetch of dpr processes.
    """
    try:
        celery_fetch_dpr()
    except Exception as e:
        logging.error("Landing task failed.", exc_info=True)
        raise self.retry(exc=e)
