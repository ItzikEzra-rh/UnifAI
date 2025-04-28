from pydantic import BaseModel, Field
from typing import Literal, Optional, Dict, Any


class LLMConfig(BaseModel):
    """
    Base schema for any LLM integration.
    """
    name: str
    type: Literal["openai", "mock", "llamastack"]
    model_name: str = Field("gpt-4", description="Model to use")
    temperature: float = Field(0.7, ge=0.0, le=1.0)
    max_tokens: int = Field(1024, description="Max tokens to generate")
    # optional overrides of transport-level params:
    api_key: Optional[str] = Field(None, description="API key or token")
    api_base: Optional[str] = Field(
        "https://api.openai.com",
        description="Base URL for the OpenAI API"
    )
    timeout: Optional[int] = Field(60, description="Request timeout in seconds")
    extra: Dict[str, Any] = Field(
        default_factory=dict,
        description="Any extra provider-specific kwargs"
    )

