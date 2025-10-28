"""
Data models for Slack event processing.

This module contains dataclasses and models used across different Slack event handlers.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass(frozen=True)
class EventContext:
    """
    Structured representation of a Slack event.
    
    Provides a consistent interface for accessing event data regardless of event type.
    """
    type: str                           # Event type (e.g., 'member_joined_channel')
    channel_id: Optional[str]           # Channel where the event occurred
    user_id: Optional[str]              # User who joined/left (or actor_id fallback)
    actor_id: Optional[str]             # User who performed the action (if present)
    event_ts: Optional[str]             # Event timestamp from Slack
    raw: Dict[str, Any]                 # Raw event data for additional fields


@dataclass(frozen=True)
class BotEventInfo:
    """
    Information about a bot-related event.
    
    Contains the essential information needed to process bot membership changes.
    """
    bot_user_id: str                    # Bot user ID from authorizations
    channel_id: str                     # Channel involved in the event
    is_member: bool                     # Whether bot is joining (True) or leaving (False)
    event_time: float                   # Resolved event timestamp
    event_type: str                     # Original event type
    actor_id: Optional[str] = None      # User who performed the action (optional)
