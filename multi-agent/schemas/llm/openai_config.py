from .llm_config import LLMConfig
from typing import Literal


class OpenAIConfig(LLMConfig):
    type: Literal["openai"]
