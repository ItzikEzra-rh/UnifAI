from typing import Literal, Optional
from elements.nodes.common.base_config import NodeBaseConfig
from pydantic import Field
from core.ref.models import Ref


class CustomAgentNodeConfig(NodeBaseConfig):
    """
    Custom agent node with full override capabilities.
    """
    llm: Ref = Field(description="LLM Ref UID to use")
