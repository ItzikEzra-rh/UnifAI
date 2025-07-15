from typing import Literal, Optional
from pydantic import Field
from elements.nodes.common.base_config import NodeBaseConfig
from core.ref.models import Ref


class MockAgentNodeConfig(NodeBaseConfig):
    """
    Allows overriding only the LLM key for the mock agent node.
    """
    type: Literal["mock_agent_node"] = "mock_agent_node"
    llm: Optional[Ref] = Field(
        None,
        description="LLM key to use for the mock agent"
    ) 