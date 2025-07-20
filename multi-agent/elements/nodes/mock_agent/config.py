from typing import Literal, Optional
from pydantic import Field
from elements.nodes.common.base_config import NodeBaseConfig
from core.ref.models import LLMRef


class MockAgentNodeConfig(NodeBaseConfig):
    """
    Allows overriding only the LLM key for the mock agent node.
    """
    llm: LLMRef = Field(None,
                        description="LLM key to use for the mock agent"
                        )
    echo_message: Optional[str] = Field(None,
                                        description="Optional fixed message to return"
                                        )
