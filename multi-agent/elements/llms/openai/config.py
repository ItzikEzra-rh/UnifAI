from typing import Literal, Dict, Any
from pydantic import Field, HttpUrl
from ..common.base_config import BaseLLMConfig


class OpenAIConfig(BaseLLMConfig):
    """
    Configuration for the official OpenAI API.
    Extracted from legacy structure and cleaned up.
    """
    model_name: str = Field(
        "Qwen/Qwen3-8B",
        description="The OpenAI model ID to use for completions"
    )
    temperature: float = Field(
        0.7, ge=0.0, le=1.0,
        description="Sampling temperature"
    )
    max_tokens: int = Field(
        4096,
        description="Maximum number of tokens to generate"
    )
    api_key: str = Field(
        "EMPTY",
        description="API key or token for OpenAI"
    )
    base_url: HttpUrl = Field(
        default_factory=lambda: HttpUrl("http://localhost:8000/v1"),
        description="Base URL for the OpenAI API"
    )
    extra: Dict[str, Any] = Field(
        default_factory=dict,
        description="Provider-specific kwargs passed through as is"
    ) 