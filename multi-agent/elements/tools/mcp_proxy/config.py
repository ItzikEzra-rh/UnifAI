from typing import Literal
from pydantic import Field
from elements.tools.common.base_config import BaseToolConfig
from core.ref.models import Ref


class McpProxyToolConfig(BaseToolConfig):
    """
    Configuration for the Mcp Proxy tool.
    """
    type: Literal["mcp_proxy"] = "mcp_proxy"
    tool_name: str = Field(..., description="mcp tool name")
    provider: Ref = Field(..., description="MCP server provider") 