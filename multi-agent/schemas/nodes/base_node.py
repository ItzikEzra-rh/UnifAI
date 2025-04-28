from pydantic import BaseModel, Field
from typing import List
from schemas.llm.llm_config import LLMConfig


class BaseNodeConfig(BaseModel):
    """
    Defines a pre-registered node's default atomic elements.
    Used by ComponentRegistry to store reusable templates.
    """
    name: str
    type: str  # e.g. "custom_agent", "tool_node"
    agent: str
    llm: str  # default LLM key
    retriever: str  # default retriever key
    tools: List[str] = []  # default tool keys
    system_message: str  # default prompt or message
