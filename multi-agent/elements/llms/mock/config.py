from typing import Optional, Literal
from pydantic import Field
from ..common.base_config import BaseLLMConfig
from .identifiers import ELEMENT_TYPE_KEY


class MockLLMConfig(BaseLLMConfig):
    """
    A "mock" LLM for testing—returns a constant or echo.
    """
    type: Literal[ELEMENT_TYPE_KEY] = ELEMENT_TYPE_KEY
    model_name: Optional[str] = Field(
        None,
        description="Ignored by the mock implementation"
    )
    constant_response: Optional[str] = Field(
        None,
        description="If set, always return this string instead of real inference"
    )
