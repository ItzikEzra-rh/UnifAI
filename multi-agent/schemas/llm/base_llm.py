from typing import ClassVar, Literal, Optional, Dict, Any, Union, Annotated, Protocol
from pydantic import BaseModel, Field, HttpUrl, Extra, SkipValidation
from core.enums import ResourceCategory


class LLMMeta(Protocol):
    category: ClassVar[ResourceCategory]
    display_name: ClassVar[str]
    description: ClassVar[str]
    type: ClassVar[str]  # discriminator value for this config


class BaseLLMConfig(BaseModel):
    """
    Common fields for any LLM provider.
    Subclasses must define a matching Literal type and can override Meta.
    """
    name: str = Field(..., description="Unique key for this LLM instance")
    type: Literal["openai", "mock", "llamastack"] = Field(
        ..., description="Discriminator: which LLM provider to use"
    )

    class Config:
        extra = Extra.forbid
        arbitrary_types_allowed = True

    class Meta(LLMMeta):
        category: ClassVar[SkipValidation[ResourceCategory]] = ResourceCategory.LLM
        display_name: ClassVar[SkipValidation[str]] = "Generic LLM"
        description: ClassVar[SkipValidation[str]] = "Base class for LLM configurations"
        type: ClassVar[SkipValidation[str]] = "base"


class OpenAIConfig(BaseLLMConfig):
    """
    Configuration for the official OpenAI API.
    """
    type: Literal["openai"] = "openai"
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

    class Meta(BaseLLMConfig.Meta):
        display_name: ClassVar[SkipValidation[str]] = "OpenAI"
        description: ClassVar[SkipValidation[str]] = "Official OpenAI API configuration"
        type: ClassVar[SkipValidation[str]] = "openai"


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

    class Meta(BaseLLMConfig.Meta):
        display_name: ClassVar[SkipValidation[str]] = "Mock LLM"
        description: ClassVar[SkipValidation[str]] = "Returns a constant or echo—for testing"
        type: ClassVar[SkipValidation[str]] = "mock"


class LlamaStackConfig(BaseLLMConfig):
    """
    Configuration for a LlamaStack inference server.
    """
    type: Literal["llamastack"] = "llamastack"
    server_url: HttpUrl = Field(
        ..., description="URL of the LlamaStack inference server"
    )
    model_id: str = Field(
        ..., description="Identifier of the Llama model to use"
    )
    timeout: Optional[int] = Field(
        60,
        description="Request timeout in seconds"
    )
    extra: Dict[str, Any] = Field(
        default_factory=dict,
        description="Provider-specific kwargs passed through as is"
    )

    class Meta(BaseLLMConfig.Meta):
        display_name: ClassVar[SkipValidation[str]] = "LlamaStack"
        description: ClassVar[SkipValidation[str]] = "LlamaStack inference server configuration"
        type: ClassVar[SkipValidation[str]] = "llamastack"


LLMsSpec = Annotated[
    Union[OpenAIConfig, MockLLMConfig, LlamaStackConfig],
    Field(discriminator="type")
]
