from typing import Literal, Union, Annotated
from pydantic import BaseModel, Field, Extra


class BaseToolConfig(BaseModel):
    """
    Common fields for any tool.
    Pure configuration schema - no UI metadata.
    
    Subclasses must define a Literal `type` field and can add specific fields.
    UI metadata is now handled by ElementSpec classes.
    """
    name: str = Field(..., description="Unique key for this tool instance")
    type: Literal["add", "divide", "ssh_exec", "mcp_proxy"] = Field(
        ..., description="Discriminator: which tool to use"
    )

    class Config:
        extra = Extra.forbid
        arbitrary_types_allowed = True
