# schemas/llm_config.py

from pydantic import BaseModel, Field, HttpUrl, Extra, validator
from typing import Literal, Optional, Dict, Any, Union, List


class BaseLLMConfig(BaseModel):
    """
    Common fields for any LLM provider.
    Concrete configs must subclass this and set `type` to a literal.
    """
    name: str = Field(..., description="Unique key for this LLM instance")
    type: Literal["openai", "mock", "llamastack"] = Field(
        ..., description="Discriminator: which LLM provider to use"
    )

    class Config:
        extra = Extra.forbid  # forbid any fields not declared here


class OpenAIConfig(BaseLLMConfig):
    """
    Configuration for the official OpenAI API.
    """
    type: Literal["openai"] = "openai"
    model_name: str = Field(
        "gpt-4",
        description="The OpenAI model ID to use for completions"
    )
    temperature: float = Field(
        0.7, ge=0.0, le=1.0,
        description="Sampling temperature"
    )
    max_tokens: int = Field(
        1024,
        description="Maximum number of tokens to generate"
    )
    api_key: str = Field(
        ..., description="API key or token for OpenAI"
    )
    api_base: HttpUrl = Field(
        "https://api.openai.com",
        description="Base URL for the OpenAI API"
    )
    azure_deployment_id: Optional[str] = Field(
        None,
        description="(Azure only) Deployment name"
    )
    timeout: Optional[int] = Field(
        60,
        description="Request timeout in seconds"
    )
    extra: Dict[str, Any] = Field(
        default_factory=dict,
        description="Provider‐specific kwargs passed through as is"
    )


class MockLLMConfig(BaseLLMConfig):
    """
    A “mock” LLM for testing—returns a constant or echo.
    """
    type: Literal["mock"] = "mock"
    model_name: Optional[str] = Field(
        None,
        description="Ignored by the mock implementation"
    )
    constant_response: Optional[str] = Field(
        None,
        description="If set, always return this string instead of real inference"
    )


class LlamaStackConfig(BaseLLMConfig):
    """
    Configuration for a LlamaStack inference server.
    """
    type: Literal["llamastack"] = "llamastack"
    server_url: HttpUrl = Field(
        ...,
        description="URL of the LlamaStack inference server"
    )
    model_id: str = Field(
        ...,
        description="Identifier of the Llama model to use"
    )
    timeout: Optional[int] = Field(
        60,
        description="Request timeout in seconds"
    )
    extra: Dict[str, Any] = Field(
        default_factory=dict,
        description="Provider‐specific kwargs passed through as is"
    )


LLMConfig = Union[OpenAIConfig, MockLLMConfig, LlamaStackConfig]


class LLMsSpec(BaseModel):
    """
    A list of LLM definitions as provided in the user blueprint.
    Uses `type` as a discriminator to pick the correct subclass.
    """
    llms: List[LLMConfig] = Field(
        ...,
        discriminator="type",
        description="Collection of LLM instances to register in this session"
    )
