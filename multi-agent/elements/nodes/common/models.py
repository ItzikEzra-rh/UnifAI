"""
Common Models for Node Elements

Shared data structures used across different node types.
"""

from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class AgentResult:
    """Result from agent processing."""
    content: str
    artifacts: Dict[str, Any] = None
    metrics: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.artifacts is None:
            self.artifacts = {}
        if self.metrics is None:
            self.metrics = {}
