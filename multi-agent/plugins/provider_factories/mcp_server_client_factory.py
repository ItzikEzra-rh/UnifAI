from typing import Any
from plugins.decorators import register_element
from plugins.base_factory import BaseFactory
from plugins.exceptions import PluginConfigurationError
from schemas.providers.base_provider import McpProviderConfig
from providers.mcp.mcp_server_client import McpServerClient


@register_element(
    category=McpProviderConfig.Meta.category,
    type_key=McpProviderConfig.Meta.type,
    config_schema=McpProviderConfig,
    description=McpProviderConfig.Meta.description
)
class McpServerClientFactory(BaseFactory[McpProviderConfig, McpServerClient]):
    """
    Factory for creating AdditionTool clients from an AdditionToolConfig.
    """

    def accepts(self, cfg: McpProviderConfig) -> bool:
        return cfg.type == "mcp_server"

    def create(self, cfg: McpProviderConfig, **kwargs: Any) -> McpServerClient:
        """
        Instantiate an AdditionToolConfig using validated config values.

        :param cfg: Fully‐validated AdditionToolConfig
        :raises PluginConfigurationError: if instantiation fails
        """
        try:
            client = McpServerClient(sse_endpoint=cfg.sse_endpoint)
            return client
        except Exception as e:
            raise PluginConfigurationError(
                f"McpServerClient.create() failed: {e}",
                cfg.dict()
            ) from e
