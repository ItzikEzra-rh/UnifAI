from typing import (
    ClassVar, Literal, Optional,
    Type, Union, Annotated, Protocol
)
from pydantic import BaseModel, Field, Extra, SkipValidation


# The Protocol your Meta classes share

class ToolMeta(Protocol):
    category: ClassVar[str]
    display_name: ClassVar[str]
    description: ClassVar[str]
    type: ClassVar[str]  # discriminator


# base tool config

class BaseToolConfig(BaseModel):
    """
    Common fields for any tool.
    Subclasses must define a Literal `type` and can override Meta.
    """
    name: str = Field(..., description="Unique key for this tool instance")
    type: Literal["base"] = Field(
        ..., description="Discriminator: which tool to use"
    )

    class Config:
        extra = Extra.forbid
        arbitrary_types_allowed = True

    class Meta(ToolMeta):
        category: ClassVar[SkipValidation[str]] = "tool"
        display_name: ClassVar[SkipValidation[str]] = "Generic Tool"
        description: ClassVar[SkipValidation[str]] = "Base class for tool configurations"
        type: ClassVar[SkipValidation[str]] = "base"


class AdditionToolConfig(BaseToolConfig):
    """
    Configuration for the “add” tool.
    """
    type: Literal["add"] = "add"

    class Meta(BaseToolConfig.Meta):
        display_name: ClassVar[SkipValidation[str]] = "Addition Tool"
        description: ClassVar[SkipValidation[str]] = "Adds two integers."
        type: ClassVar[SkipValidation[str]] = "add"


# Union of all tool configs, discriminated by `type`

ToolsSpec = Annotated[
    Union[
        AdditionToolConfig,
    ],
    Field(discriminator="type")
]
