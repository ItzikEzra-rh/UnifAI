"""
MCP Server Client Actions

This package contains all actions available for the MCP server client element.
Each action follows SOLID principles and has a single, clear responsibility.
"""

from .validate_connection import ValidateConnectionAction
from .get_tools_names import GetToolsNamesAction

__all__ = [
    "ValidateConnectionAction",
    "GetToolsNamesAction"
]