from pydantic import BaseModel, Field, Optional
from typing import List
from schemas.llm.llm_config import LLMConfig


class BaseNodeConfig(BaseModel):
    """
    A reusable “template” for a Node, registered in ElementRegistry.
    Provides default atomic keys.
    """
    name: str
    type: str  # must match NodeSpec.type
    llm: str  # default LLM key
    retriever: Optional[str]
    tools: List[str] = []
    system_message: Optional[str]
    retries: int = 1
