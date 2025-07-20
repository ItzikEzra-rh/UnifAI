from typing import Optional
from elements.nodes.common.base_config import NodeBaseConfig
from pydantic import Field


class FinalAnswerNodeConfig(NodeBaseConfig):
    """
    Emits the final aggregated answer without overrides.
    """
    name: str = Field(None, description="Optional node instance name")
