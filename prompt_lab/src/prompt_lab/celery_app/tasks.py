from prompt_lab.celery_app import CeleryApp
from prompt_lab.tasks import run_orbiter, run_landing
from prompt_lab.utils import logger


@CeleryApp().app.task(bind=True, max_retries=16, default_retry_delay=30)  # 8 minutes till fail
def orbiter(self, batch):
    """
    Celery task for the orbiter process with retry logic.
    """
    try:
        run_orbiter(batch)
    except Exception as e:
        logger.error("Orbiter task failed.", exc_info=True)
        raise self.retry(exc=e)


@CeleryApp().app.task(bind=True, max_retries=16, default_retry_delay=30)  # 8 minutes till fail
def landing(self, batch):
    """
    Celery task for the landing process with retry logic.
    """
    try:
        run_landing(batch)
    except Exception as e:
        logger.error("Landing task failed.", exc_info=True)
        raise self.retry(exc=e)
