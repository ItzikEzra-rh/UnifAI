from typing import Literal
from .identifiers import Identifier
from pydantic import Field, HttpUrl
from elements.providers.common.base_config import ProviderBaseConfig


class McpProviderConfig(ProviderBaseConfig):
    """
    Connects to a Model-Context-Protocol service that exposes both
    WebSocket & SSE endpoints.
    """
    type: Literal[Identifier.TYPE] = Identifier.TYPE
    sse_endpoint: HttpUrl = Field(
        ...,
        description="HTTP(S) endpoint that streams SSE events",
        example="https://api.example.com:8000/"
    )
