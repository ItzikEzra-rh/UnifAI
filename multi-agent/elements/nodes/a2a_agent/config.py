"""
A2A Agent Node Configuration
"""

from elements.nodes.common.base_config import NodeBaseConfig
from pydantic import Field, HttpUrl
from typing import Optional, Literal
from a2a.types import AgentCard
from .identifiers import Identifier
from core.ref.models import RetrieverRef


class A2AAgentNodeConfig(NodeBaseConfig):
    """
    A2A Agent Node - delegates work to remote agent via A2A protocol.
    
    Simple configuration with just endpoint and optional retriever.
    The node creates its own A2A provider internally.
    """
    type: Literal[Identifier.TYPE] = Identifier.TYPE
    
    base_url: HttpUrl = Field(
        description="Base URL of the A2A agent (e.g., http://localhost:10000)"
    )
    
    agent_card: Optional[AgentCard] = Field(
        default=None,
        description="Pre-fetched agent card (optional, will be fetched if not provided)"
    )
    
    retriever: Optional[RetrieverRef] = Field(
        None, 
        description="Retriever for context augmentation (optional)"
    )

