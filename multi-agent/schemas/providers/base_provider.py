from typing import ClassVar, Literal, Optional, Union, Annotated, Protocol
from pydantic import BaseModel, Field, Extra, HttpUrl, SecretStr, SkipValidation
from core.enums import ResourceCategory


class ProviderMeta(Protocol):
    category: ClassVar[str]
    display_name: ClassVar[str]
    description: ClassVar[str]
    type: ClassVar[str]


class ProviderBaseConfig(BaseModel):
    """
    Common fields for any provider implementation.
    """
    name: str = Field(..., description="Unique key for this provider instance")
    type: str = Field(..., description="Discriminator used by plugins")

    class Config:
        extra = Extra.forbid
        arbitrary_types_allowed = True

    class Meta(ProviderMeta):
        category: ClassVar[SkipValidation[str]] = ResourceCategory.PROVIDER
        display_name: ClassVar[SkipValidation[str]] = "Base Provider"
        description: ClassVar[SkipValidation[str]] = "Abstract base for all providers"
        type: ClassVar[SkipValidation[str]] = "base"


# --------------------------------------------------------------------------
# Concrete provider: MCP Web-Socket / SSE server
# --------------------------------------------------------------------------
class McpProviderConfig(ProviderBaseConfig):
    """
    Connects to a Model-Context-Protocol service that exposes both
    WebSocket & SSE endpoints.
    """
    type: Literal["mcp_server"] = "mcp_server"

    # Endpoints ------------------------------------------------------------
    sse_endpoint: HttpUrl = Field(
        ...,
        description="HTTP(S) endpoint that streams SSE events",
        example="https://api.example.com:8000/sse"
    )

    class Meta(ProviderBaseConfig.Meta):
        display_name: ClassVar[SkipValidation[str]] = "MCP Server Provider"
        description: ClassVar[SkipValidation[str]] = "Remote MCP service via WebSocket / SSE"
        type: ClassVar[SkipValidation[str]] = "mcp_server"


ProviderSpec = Annotated[
    Union[McpProviderConfig],
    Field(discriminator="type")
]
