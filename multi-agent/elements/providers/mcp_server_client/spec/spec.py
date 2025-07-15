from typing import ClassVar
from elements.common.base_element_spec import BaseElementSpec
from core.enums import ResourceCategory
from ..config import McpProviderConfig
from ..mcp_server_client_factory import McpServerClientFactory


class McpServerClientElementSpec(BaseElementSpec):
    """Element specification for MCP Server Client Provider."""

    category: ClassVar[ResourceCategory] = ResourceCategory.PROVIDER
    type_key = "mcp_server"
    name = "MCP Server Provider"
    description = "Remote MCP service via HTTPS/SSE"
    config_schema = McpProviderConfig
    factory_cls = McpServerClientFactory
    tags = ["provider", "mcp", "server", "client", "websocket", "sse"]
