from typing import Any
from elements.common.base_factory import BaseFactory
from elements.common.exceptions import PluginConfigurationError
from .config import McpProviderConfig
from .mcp_server_client import McpServerClient
from .identifiers import Identifier


class McpServerClientFactory(BaseFactory[McpProviderConfig, McpServerClient]):
    """
    Factory for creating AdditionTool clients from an AdditionToolConfig.
    """

    def accepts(self, cfg: McpProviderConfig, element_type: str) -> bool:
        return element_type == Identifier.TYPE

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
