from pydantic import BaseModel, Field
from typing import List, Literal


class AgentConfig(BaseModel):
    """
    Configuration for a custom agent node, which wraps an LLM, tools, and a retriever.

    Attributes:
        name: Unique name for this agent node (appears in the graph).
        type: Must be "custom_agent" for this schema.
        llm: Key of the LLM to use (resolved via PluginRegistry).
        tools: List of tool names to inject into the agent.
        retriever: Name of the data-source retriever to use.
        system_message: The system prompt or initial message for the LLM.
    """
    name: str
    type: Literal["custom_agent"] = Field("custom_agent", const=True)
    llm: str
    tools: List[str] = []
    retriever: str
    system_message: str
