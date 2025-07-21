from typing import ClassVar
from elements.common.base_element_spec import BaseElementSpec
from core.enums import ResourceCategory
from ..config import McpProviderConfig
from ..mcp_server_client_factory import McpServerClientFactory
from ..identifiers import Identifier, META


class McpServerClientElementSpec(BaseElementSpec):
    """Element specification for MCP Server Client Provider."""

    category: ClassVar[ResourceCategory] = ResourceCategory.PROVIDER
    type_key = Identifier.TYPE
    name = META.name
    description = META.description
    config_schema = McpProviderConfig
    factory_cls = McpServerClientFactory
    tags = META.tags
