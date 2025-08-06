from typing import ClassVar, Type, List
from elements.common.base_element_spec import BaseElementSpec
from elements.common.actions import BaseAction
from core.enums import ResourceCategory
from ..config import McpProviderConfig
from ..mcp_server_client_factory import McpServerClientFactory
from ..identifiers import Identifier, META
from ..actions import ValidateConnectionAction, GetToolsNamesAction


class McpServerClientElementSpec(BaseElementSpec):
    """
    Element specification for MCP Server Client Provider with actions.
    
    Provides validation, discovery, and utility actions for MCP server connections.
    Demonstrates both sync and async action execution patterns.
    """

    category: ClassVar[ResourceCategory] = ResourceCategory.PROVIDER
    type_key = Identifier.TYPE
    name = META.name
    description = META.description
    config_schema = McpProviderConfig
    factory_cls = McpServerClientFactory
    tags = META.tags
    actions: ClassVar[List[Type[BaseAction]]] = [
        ValidateConnectionAction,
        GetToolsNamesAction,
    ]