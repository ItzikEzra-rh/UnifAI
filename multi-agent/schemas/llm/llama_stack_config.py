from .llm_config import LLMConfig
from typing import Literal


class LlamaStackConfig(LLMConfig):
    type: Literal["llamastack"]
    # e.g. host: str, port: int if needed
