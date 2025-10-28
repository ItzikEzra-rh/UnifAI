"""
Slack Events API service module.

Handles processing of Slack Events API callbacks.
"""

from .processor import process_event, register_event_handler

__all__ = ['process_event', 'register_event_handler']
