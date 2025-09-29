"""
Common Models for Node Elements

Shared data structures used across different node types.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from pydantic import BaseModel, Field
from datetime import datetime


@dataclass
class AgentResult:
    """Result from agent processing."""
    content: str
    agent_id: str
    agent_name: str
    artifacts: Dict[str, Any] = None
    metrics: Dict[str, Any] = None
    success: bool = True
    error: Optional[str] = None
    reasoning: str = ""
    execution_metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.artifacts is None:
            self.artifacts = {}
        if self.metrics is None:
            self.metrics = {}
        if self.execution_metadata is None:
            self.execution_metadata = {}



class ArtifactRef(BaseModel):
    """Reference to an artifact with metadata."""
    name: str
    type: str
    location: str
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


# WorkspaceContext moved to task.py to avoid circular imports
