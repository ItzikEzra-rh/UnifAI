from typing import (
    ClassVar, Literal, Optional,
    Type, Union, Annotated, Protocol
)
from pydantic import BaseModel, Field, Extra, SkipValidation
from core.enums import ResourceCategory


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
        category: ClassVar[SkipValidation[str]] = ResourceCategory.TOOL
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


class DivisionToolConfig(BaseToolConfig):
    """
    Configuration for the “divide” tool.
    """
    type: Literal["divide"] = "divide"

    class Meta(BaseToolConfig.Meta):
        display_name: ClassVar[SkipValidation[str]] = "Division Tool"
        description: ClassVar[SkipValidation[str]] = "divide two numbers."
        type: ClassVar[SkipValidation[str]] = "divide"


class SshExecToolConfig(BaseToolConfig):
    """
    Configuration for the SSH-execution tool.
    """
    type: Literal["ssh_exec"] = "ssh_exec"
    host: str = Field(..., description="IP or DNS name of the target VM")
    port: int = Field(22, description="SSH port")
    username: str = Field(..., description="SSH user name")
    password: str = Field(..., description="SSH password (store in secret manager!)")

    class Meta(BaseToolConfig.Meta):
        display_name: ClassVar[SkipValidation[str]] = "SSH Exec"
        description: ClassVar[SkipValidation[str]] = "Execute a shell command on a remote VM"
        type: ClassVar[SkipValidation[str]] = "ssh_exec"


# Union of all tool configs, discriminated by `type`

ToolsSpec = Annotated[
    Union[
        AdditionToolConfig,
        DivisionToolConfig,
        SshExecToolConfig
    ],
    Field(discriminator="type")
]
