from .base_agent_config import BaseAgentConfig
from typing import Literal


class MockAgentConfig(BaseAgentConfig):
    """
    Configuration schema for a Mock Agent.
    A mock agent is usually used for testing purposes.
    """
    type: Literal["mock_agent"]
    llm: Literal["mock_llm"]
