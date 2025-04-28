from .llm_config import LLMConfig
from typing import Literal


class MockLLMConfig(LLMConfig):
    type: Literal["mock"]
