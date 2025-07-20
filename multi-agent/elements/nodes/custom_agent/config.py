from elements.nodes.common.base_config import NodeBaseConfig
from pydantic import Field
from typing import Optional, List, Literal
from .identifiers import ELEMENT_TYPE_KEY
from core.ref.models import LLMRef, RetrieverRef, ToolRef


class CustomAgentNodeConfig(NodeBaseConfig):
    """
    Custom agent node with full override capabilities.
    """
    type: Literal[ELEMENT_TYPE_KEY] = ELEMENT_TYPE_KEY
    llm: LLMRef = Field(description="LLM Ref UID to use")
    retriever: Optional[RetrieverRef] = Field(None, description="Retriever key to use")
    tools: Optional[List[ToolRef]] = Field(default_factory=list, description="List of tool keys")
    system_message: str = Field(None, description="Custom system prompt")
