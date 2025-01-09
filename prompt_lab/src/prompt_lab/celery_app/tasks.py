from prompt_lab.celery_app import CeleryApp
from prompt_lab.tasks import run_orbiter, run_landing


@CeleryApp().app.task(bind=True, max_retries=16, default_retry_delay=30)  # 8 minutes till fail
def orbiter(self, batch):
    """
    Celery task for the orbiter process with retry logic.
    """
    try:
        run_orbiter(batch)  # Your existing task logic
    except Exception as e:
        # Log the exception and retry the task
        print(f"Orbiter task failed: {e}. Retrying...")
        raise self.retry(exc=e)


@CeleryApp().app.task(bind=True, max_retries=16, default_retry_delay=30)  # 8 minutes till fail
def landing(self, batch):
    """
    Celery task for the landing process with retry logic.
    """
    try:
        run_landing(batch)  # Your existing task logic
    except Exception as e:
        # Log the exception and retry the task
        print(f"Landing task failed: {e}. Retrying...")
        raise self.retry(exc=e)
