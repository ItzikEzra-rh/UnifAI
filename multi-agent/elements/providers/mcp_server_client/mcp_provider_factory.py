from typing import Any
from elements.common.base_factory import BaseFactory
from elements.common.exceptions import PluginConfigurationError
from global_utils.utils.util import run_async
from .config import McpProviderConfig
from .mcp_provider import McpProvider
from .identifiers import Identifier


class McpProviderFactory(BaseFactory[McpProviderConfig, McpProvider]):
    """
    Factory for creating MCP Provider instances from McpProviderConfig.
    """

    def accepts(self, cfg: McpProviderConfig, element_type: str) -> bool:
        return element_type == Identifier.TYPE

    def create(self, cfg: McpProviderConfig, **kwargs: Any) -> McpProvider:
        """
        Instantiate an McpProvider using validated config values.

        :param cfg: Fully‐validated McpProviderConfig
        :raises PluginConfigurationError: if instantiation fails
        """
        try:
            provider = McpProvider(
                sse_endpoint=cfg.sse_endpoint,
                tool_names=cfg.tool_names
            )
            run_async(provider._initialize_tools())
            return provider
        except Exception as e:
            raise PluginConfigurationError(
                f"McpProvider.create() failed: {e}",
                cfg.dict()
            ) from e