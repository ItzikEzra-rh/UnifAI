from pydantic import BaseModel, Field, Extra


class BaseRetrieverConfig(BaseModel):
    """
    Common fields for any Retriever.
    Pure configuration schema - no UI metadata.
    
    Subclasses must set `type` Literal and can add specific fields.
    UI metadata is now handled by ElementSpec classes.
    """
    name: str = Field(..., description="Unique key for this retriever instance")
    type: str = Field(
        ..., description="Discriminator: which retriever provider to use"
    )

    class Config:
        extra = Extra.forbid
        arbitrary_types_allowed = True
