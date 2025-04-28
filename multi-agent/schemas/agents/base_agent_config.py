from pydantic import BaseModel
from typing import List


class BaseAgentConfig(BaseModel):
    """
    Base configuration for any agent node.
    Includes common fields shared across all agent types.
    """
    name: str
    type: str
    llm: str
    tools: List[str] = []
    retriever: str
    system_message: str
    retries: int = 1  # Default retries to 1
