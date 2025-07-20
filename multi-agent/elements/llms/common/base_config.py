from typing import Literal, Union, Annotated
from pydantic import BaseModel, Field, Extra


class BaseLLMConfig(BaseModel):
    """
    Common fields for any LLM provider.
    Pure configuration schema - no UI metadata.
    
    Subclasses must define a matching Literal type field for discrimination.
    UI metadata is now handled by ElementSpec classes.
    """
    name: str = Field(..., description="Unique key for this LLM instance")

    class Config:
        extra = Extra.forbid
        arbitrary_types_allowed = True
