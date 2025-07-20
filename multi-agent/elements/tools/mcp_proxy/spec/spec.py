from elements.common.base_element_spec import BaseElementSpec
from core.enums import ResourceCategory
from ..config import McpProxyToolConfig
from ..mcp_proxy_factory import McpProxyToolFactory
from ..identifiers import ELEMENT_TYPE_KEY


class McpProxyToolElementSpec(BaseElementSpec):
    """Element specification for MCP Proxy Tool."""

    category = ResourceCategory.TOOL
    type_key = ELEMENT_TYPE_KEY
    name = "MCP Proxy Tool"
    description = "Execute a MCP tool through MCP Server Provider"
    config_schema = McpProxyToolConfig
    factory_cls = McpProxyToolFactory
    tags = ["tool", "mcp", "proxy", "remote", "execution"]
