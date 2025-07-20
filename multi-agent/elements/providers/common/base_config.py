from typing import Union, Annotated
from pydantic import BaseModel, Field, Extra


class ProviderBaseConfig(BaseModel):
    """
    Common fields for any provider implementation.
    Pure configuration schema - no UI metadata.
    
    UI metadata is now handled by ElementSpec classes.
    """
    name: str = Field(..., description="Unique key for this provider instance")

    class Config:
        extra = Extra.forbid
        arbitrary_types_allowed = True
