"""
Slack user event manager for handling bot membership changes.

Behavior preserved:
- Bot user id comes from payload.authorizations[0].user_id
- Event time = event.event_ts -> payload.event_time -> now
- Only process events that are about the bot joining/leaving
- Ensure channel exists; update is_app_member + last_updated
- If channel missing: try conversations.info; else insert minimal doc
- Project resolution: use default project else prepare 'slack-events-default'
"""

from typing import Dict, Any
from shared.logger import logger
from .slack_event_helpers import (
    extract_event,
    get_bot_user_id,
    is_bot_event,
    create_bot_event_info,
    log_bot_event,
    BOT_MEMBERSHIP_EVENT_RULES
)
from .slack_channel_service import SlackChannelStorageService


class SlackUserManager:
    """
    Handles Slack bot membership events.
    
    Processes bot join/leave events and maintains channel membership status in MongoDB.
    Uses repository pattern for data access and helper functions for event processing.
    """

    def __init__(self):
        self._storage_service = SlackChannelStorageService()

    def handle_member_joined(self, payload: Dict[str, Any]) -> None:
        """Handle member_joined_channel event (backward compatibility)."""
        self.handle(payload)

    def handle_member_left(self, payload: Dict[str, Any]) -> None:
        """Handle member_left_channel/channel_left/group_left events (backward compatibility)."""
        self.handle(payload)

    def handle(self, payload: Dict[str, Any]) -> None:
        """
        Main event handler for all bot membership events.
        
        Args:
            payload: Full Slack event payload
        """
        # Extract and validate event context
        ctx = extract_event(payload)
        if not ctx.type:
            logger.warning("Missing event type in payload.event")
            return

        # Check if this event is about our bot
        bot_user_id = get_bot_user_id(payload)
        is_about_bot, action = is_bot_event(ctx, bot_user_id or "", BOT_MEMBERSHIP_EVENT_RULES)
        
        if not is_about_bot:
            self._log_ignored_event(ctx, bot_user_id)
            return

        # Create structured event info
        event_info = create_bot_event_info(payload, ctx, action)
        if not event_info:
            return

        # Log the event
        log_bot_event(event_info)

        # Update channel membership via service
        success = self._storage_service.get_or_create_channel(
            channel_id=event_info.channel_id,
            is_member=event_info.is_member,
            timestamp=event_info.event_time
        )

        # Log final result
        if success:
            logger.info(f"Successfully processed {event_info.event_type} for channel {event_info.channel_id} (bot_member={event_info.is_member})")
        else:
            logger.error(f"Failed to process {event_info.event_type} for channel {event_info.channel_id}")

    def _log_ignored_event(self, ctx, bot_user_id: str) -> None:
        """Log why an event was ignored."""
        if ctx.type in BOT_MEMBERSHIP_EVENT_RULES:
            logger.info(f"Ignoring {ctx.type}: not about our bot (bot={bot_user_id}, user={ctx.user_id})")
        else:
            logger.debug(f"Unhandled event type in SlackUserManager: {ctx.type}")
