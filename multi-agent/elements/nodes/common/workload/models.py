"""
Common Models for Node Elements

Shared data structures used across different node types.
"""

from typing import Dict, Any, List, TYPE_CHECKING
from dataclasses import dataclass
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from elements.llms.common.chat.message import ChatMessage
    from .workspace import ArtifactRef


@dataclass
class AgentResult:
    """Result from agent processing."""
    content: str
    agent_id: str
    agent_name: str
    artifacts: Dict[str, Any] = None
    metrics: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.artifacts is None:
            self.artifacts = {}
        if self.metrics is None:
            self.metrics = {}


class WorkspaceContext(BaseModel):
    """
    Workspace context data model.
    
    Contains all shared context data for a workspace.
    """
    # Shared Context Data
    facts: List[str] = Field(default_factory=list)
    results: List[AgentResult] = Field(default_factory=list)
    artifacts: Dict[str, 'ArtifactRef'] = Field(default_factory=dict)
    variables: Dict[str, Any] = Field(default_factory=dict)
    conversation_history: List['ChatMessage'] = Field(default_factory=list)
