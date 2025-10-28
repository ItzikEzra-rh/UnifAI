"""
Celery tasks for Slack event subscriptions.
"""
from typing import Dict, Any
from global_utils.celery_app import CeleryApp
from shared.logger import logger
from services.slack_events.processor import process_event


@CeleryApp().app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_slack_events_task(self, payload: Dict[str, Any]):
    """
    Celery task to process Slack Events API callbacks.
    
    Args:
        payload: Full Slack event payload
    """
    try:
        process_event(payload)
    except Exception as e:
        logger.error(f"Error processing Slack event {payload.get('event_id')}: {e}", exc_info=True)
        raise self.retry(exc=e)


