from typing import Any, Dict
from pydantic import BaseModel, Field, ConfigDict

from mas.blueprints.models.blueprint import StepMeta
from .adjacency import AdjacentNodes
from ..topology.models import StepTopology


class StepContext(BaseModel):
    """Immutable context object injected into nodes / conditions at runtime."""

    uid: str
    metadata: StepMeta = Field(default_factory=StepMeta)
    adjacent_nodes: AdjacentNodes = Field(default_factory=AdjacentNodes.empty)
    branches: Dict[str, str] = Field(default_factory=dict)
    topology: StepTopology = Field(default_factory=StepTopology)

    model_config = ConfigDict(frozen=True)

    def serialize(self) -> Dict[str, Any]:
        """Convert to a JSON-safe dict for cross-process transport."""
        return self.model_dump(mode="json")

    @classmethod
    def deserialize(cls, data: Dict[str, Any]) -> "StepContext":
        """Reconstruct a StepContext from a serialized dict."""
        return cls.model_validate(data)
