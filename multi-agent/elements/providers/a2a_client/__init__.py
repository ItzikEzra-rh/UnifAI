"""
A2A Provider Package

Provides clean interface for communicating with A2A (Agent-to-Agent) protocol agents.
Uses official a2a-sdk internally.
"""

from .a2a_provider import A2AProvider
from .a2a_provider_factory import A2AProviderFactory
from .a2a_client import A2AClient, A2AConnectionError
from .message_converter import A2AMessageConverter
from .config import A2AProviderConfig
from .identifiers import Identifier, META

__all__ = [
    "A2AProvider",
    "A2AProviderFactory",
    "A2AClient",
    "A2AConnectionError",
    "A2AMessageConverter",
    "A2AProviderConfig",
    "Identifier",
    "META",
]

