from pydantic import BaseModel
from typing import List, Union

from schemas.llm_config import LLMConfig
from schemas.tool_config import (
    CalculatorConfig, WeatherConfig,
    HTTPToolConfig, MCPToolConfig, WebSearchConfig
)
from schemas.retriever_config import (
    SlackRetrieverConfig, JiraRetrieverConfig, PDFRetrieverConfig
)
from schemas.agent_config import AgentConfig
from schemas.node_config import NodeSpec

# Union types for top-level lists
ToolConfig = Union[
    CalculatorConfig, WeatherConfig,
    HTTPToolConfig, MCPToolConfig, WebSearchConfig
]
RetrieverConfig = Union[
    SlackRetrieverConfig, JiraRetrieverConfig, PDFRetrieverConfig
]


class StepSpec(BaseModel):
    """
    Defines a single step in the blueprint plan.
    """
    name: str
    after: Union[str, List[str]] = None
    node: Union[str, NodeSpec]


class Blueprint(BaseModel):
    """
    Full blueprint schema, including dynamic component definitions
    and an ordered list of steps.
    """
    llms: List[LLMConfig] = []
    tools: List[ToolConfig] = []
    retrievers: List[RetrieverConfig] = []
    agents: List[AgentConfig] = []
    plan: List[StepSpec]
