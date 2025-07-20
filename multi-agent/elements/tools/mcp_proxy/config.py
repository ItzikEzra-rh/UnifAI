from typing import Literal
from pydantic import Field
from elements.tools.common.base_config import BaseToolConfig
from core.ref.models import ProviderRef
from .identifiers import ELEMENT_TYPE_KEY


class McpProxyToolConfig(BaseToolConfig):
    """
    Configuration for the Mcp Proxy tool.
    """
    type: Literal[ELEMENT_TYPE_KEY] = ELEMENT_TYPE_KEY
    tool_name: str = Field(..., description="")
    provider: ProviderRef = Field(..., description="MCP server provider")
