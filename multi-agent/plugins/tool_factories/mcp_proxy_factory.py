from typing import Any
from plugins.decorators import register_element
from plugins.base_factory import BaseFactory
from plugins.exceptions import PluginConfigurationError
from tools.models.tool_config import McpProxyToolConfig
from tools.mcp_tool import McpProxyTool
from providers.mcp.mcp_server_client import McpServerClient


@register_element(
    category=McpProxyToolConfig.Meta.category,
    type_key=McpProxyToolConfig.Meta.type,
    config_schema=McpProxyToolConfig,
    description=McpProxyToolConfig.Meta.description
)
class McpProxyToolFactory(BaseFactory[McpProxyToolConfig, McpProxyTool]):
    """
    Factory for creating Division clients from an DivisionToolConfig.
    """

    def accepts(self, cfg: McpProxyToolConfig) -> bool:
        return cfg.type == "mcp_proxy"

    def create(self, cfg: McpProxyToolConfig, **kwargs: Any) -> McpProxyTool:
        try:
            provider: McpServerClient = kwargs.get("provider")
            client = McpProxyTool(mcp_tool_name=cfg.tool_name, mcp_client=provider)
            return client
        except Exception as e:
            raise PluginConfigurationError(
                f"McpProxyTool.create() failed: {e}",
                cfg.dict()
            ) from e
