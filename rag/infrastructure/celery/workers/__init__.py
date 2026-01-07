"""Celery workers (driving adapters) - receive tasks from queue and delegate to application."""
from infrastructure.celery.workers.pipeline_tasks import execute_pipeline_task

__all__ = ["execute_pipeline_task"]

