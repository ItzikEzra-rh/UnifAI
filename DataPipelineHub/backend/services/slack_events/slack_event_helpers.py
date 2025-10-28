"""
Helper functions for Slack event processing.

This module contains utility functions that can be reused across different Slack event handlers.
"""

from typing import Dict, Any, Optional, Callable, Tuple
import time
from shared.logger import logger
from .slack_event_models import EventContext, BotEventInfo


def extract_event(payload: Dict[str, Any]) -> EventContext:
    """
    Extract structured event context from Slack payload.
    
    Args:
        payload: Full Slack event payload
        
    Returns:
        EventContext with parsed event data
    """
    e = payload.get("event") or {}
    return EventContext(
        type=e.get("type"),
        channel_id=e.get("channel"),
        user_id=e.get("user") or e.get("actor_id"),
        actor_id=e.get("actor_id"),
        event_ts=e.get("event_ts"),
        raw=e,
    )


def get_bot_user_id(payload: Dict[str, Any]) -> Optional[str]:
    """
    Extract bot user ID from Slack event payload.
    
    Args:
        payload: Full Slack event payload
        
    Returns:
        Bot user ID from authorizations, or None if not found
    """
    auth = payload.get("authorizations") or []
    if auth and isinstance(auth, list):
        return auth[0].get("user_id")
    return None


def resolve_event_time(payload: Dict[str, Any], ctx: EventContext) -> float:
    """
    Resolve event timestamp from payload or context.
    
    Priority: event.event_ts -> payload.event_time -> current time
    
    Args:
        payload: Full Slack event payload
        ctx: Event context
        
    Returns:
        Event timestamp as float
    """
    if ctx.event_ts:
        try:
            return float(ctx.event_ts)
        except (ValueError, TypeError):
            logger.warning(f"Invalid event_ts '{ctx.event_ts}', falling back to payload.event_time")
    
    et = payload.get("event_time")
    if et is not None:
        try:
            return float(et)
        except (ValueError, TypeError):
            logger.warning(f"Invalid event_time '{et}', using current time")
    
    return time.time()


def is_bot_event(ctx: EventContext, bot_user_id: str, event_rules: Dict[str, Tuple[str, Callable[[EventContext, str], bool]]]) -> Tuple[bool, Optional[str]]:
    """
    Check if an event is about the bot and determine the action type.
    
    Args:
        ctx: Event context
        bot_user_id: Bot user ID
        event_rules: Dictionary mapping event types to (action, predicate) tuples
        
    Returns:
        Tuple of (is_about_bot, action_type)
        action_type is 'join', 'leave', or None
    """
    rule = event_rules.get(ctx.type)
    if not rule:
        return False, None
    
    action, is_about_bot_predicate = rule
    if is_about_bot_predicate(ctx, bot_user_id):
        return True, action
    
    return False, None


def create_bot_event_info(payload: Dict[str, Any], ctx: EventContext, action: str) -> Optional[BotEventInfo]:
    """
    Create BotEventInfo from payload and context.
    
    Args:
        payload: Full Slack event payload
        ctx: Event context
        action: Action type ('join' or 'leave')
        
    Returns:
        BotEventInfo or None if required data is missing
    """
    bot_user_id = get_bot_user_id(payload)
    if not bot_user_id:
        logger.error(f"No bot user ID in payload for event {payload.get('event_id')}")
        return None
    
    if not ctx.channel_id:
        logger.warning(f"Missing channel in {ctx.type} event: {ctx.raw}")
        return None
    
    event_time = resolve_event_time(payload, ctx)
    is_member = (action == "join")
    
    return BotEventInfo(
        bot_user_id=bot_user_id,
        channel_id=ctx.channel_id,
        is_member=is_member,
        event_time=event_time,
        event_type=ctx.type,
        actor_id=ctx.actor_id
    )


def log_bot_event(event_info: BotEventInfo) -> None:
    """
    Log bot event information in a consistent format.
    
    Args:
        event_info: Bot event information
    """
    action = "joined" if event_info.is_member else "left/was removed from"
    channel_type = "private" if event_info.event_type == "group_left" else "public"
    
    actor_msg = f" by user {event_info.actor_id}" if event_info.actor_id else ""
    
    logger.info(f"Bot {event_info.bot_user_id} {action} {channel_type} channel {event_info.channel_id}{actor_msg}")


# Common event rules for bot membership events
BOT_MEMBERSHIP_EVENT_RULES: Dict[str, Tuple[str, Callable[[EventContext, str], bool]]] = {
    "member_joined_channel": ("join",  lambda ctx, bot: (ctx.user_id == bot)),
    "member_left_channel":   ("leave", lambda ctx, bot: (ctx.user_id == bot)),
    "channel_left":          ("leave", lambda ctx, bot: True),  # Bot leaves public channel (by definition)
    "group_left":            ("leave", lambda ctx, bot: (ctx.user_id == bot)),  # Private channel
}
