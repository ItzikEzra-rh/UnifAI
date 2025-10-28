"""
Main event processor for Slack Events API.

Provides event routing, de-duplication, and handler registration.
"""

from typing import Dict, Any, Callable, Optional
import time
from shared.logger import logger
from .deduplication import is_event_processed
from .slack_user_manager import SlackUserManager


class SlackEventProcessor:
    """
    Central processor for Slack events with pluggable handlers.
    
    Handles de-duplication, routing, and provides a registry for custom event handlers.
    """
    
    def __init__(self):
        self._user_manager = SlackUserManager()
        self._handlers: Dict[str, Callable[[Dict[str, Any]], None]] = {}
        self._setup_default_handlers()
    
    def _setup_default_handlers(self) -> None:
        """Setup default handlers for bot membership events."""
        bot_membership_events = [
            "member_joined_channel",
            "member_left_channel", 
            "channel_left",
            "group_left"
        ]
        
        for event_type in bot_membership_events:
            self._handlers[event_type] = self._user_manager.handle
    
    def register_handler(self, event_type: str, handler: Callable[[Dict[str, Any]], None]) -> None:
        """
        Register a custom handler for a specific event type.
        
        Args:
            event_type: Slack event type to handle
            handler: Function that takes the full event payload
        """
        self._handlers[event_type] = handler
        logger.info(f"Registered custom handler for event type: {event_type}")
    
    def get_handler(self, event_type: str) -> Optional[Callable[[Dict[str, Any]], None]]:
        """
        Get handler for an event type.
        
        Args:
            event_type: Slack event type
            
        Returns:
            Handler function or None if not found
        """
        return self._handlers.get(event_type)
    
    def process_event(self, payload: Dict[str, Any]) -> bool:
        """
        Process a Slack event payload with de-duplication and dispatch.
        
        Args:
            payload: Full Slack event payload
            
        Returns:
            True if event was processed successfully
        """
        # Extract event metadata
        event_id = payload.get("event_id")
        event_data = payload.get("event", {}) or {}
        event_type = event_data.get("type")
        event_time = payload.get("event_time", time.time())

        # Validate required fields
        if not event_id:
            logger.error("No event_id in payload, cannot process")
            return False

        logger.info(f"Processing Slack event {event_id} of type {event_type}")
        if is_event_processed(event_id):
            logger.info(f"Event {event_id} already processed, skipping")
            return True

        handler = self.get_handler(event_type)
        if not handler:
            logger.debug(f"No handler registered for event type: {event_type}")
            return False

        try:
            handler(payload)
            logger.info(f"Successfully processed Slack event {event_id} at {event_time}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing Slack event {event_id}: {e}", exc_info=True)
            return False


# Global processor instance
_processor = SlackEventProcessor()

def process_event(payload: Dict[str, Any]) -> None:
    """Process a Slack event (backward compatibility function)."""
    _processor.process_event(payload)
