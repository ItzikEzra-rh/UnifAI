from typing import Literal
from pydantic import Field
from elements.tools.common.base_config import BaseToolConfig
from core.ref.models import ProviderRef
from .identifiers import Identifier


class McpProxyToolConfig(BaseToolConfig):
    """
    Configuration for the Mcp Proxy tool.
    """
    type: Literal[Identifier.TYPE] = Identifier.TYPE
    tool_name: str = Field(..., description="")
    provider: ProviderRef = Field(..., description="MCP server provider")
