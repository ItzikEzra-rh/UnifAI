"""
Slack Events API service module.

Handles processing of Slack Events API callbacks.
"""

from .processor import process_event

__all__ = ['process_event']
