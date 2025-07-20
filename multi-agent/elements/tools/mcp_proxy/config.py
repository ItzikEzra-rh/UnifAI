from typing import Literal
from pydantic import Field
from elements.tools.common.base_config import BaseToolConfig
from core.ref.models import ProviderRef


class McpProxyToolConfig(BaseToolConfig):
    """
    Configuration for the Mcp Proxy tool.
    """
    type: Literal["mcp_proxy"] = "mcp_proxy"
    tool_name: str = Field(..., description="")
    provider: ProviderRef = Field(..., description="MCP server provider")
