# plugins/tool_factories/mcp_factory.py

from typing import Any, Dict, Literal
from pydantic import BaseModel, ValidationError, HttpUrl
from plugins.base_factory import BaseFactory
from plugins.exceptions import PluginConfigurationError
from tools.mcp_tool_adapter import MCPToolAdapter


class MCPToolConfig(BaseModel):
    """
    Configuration schema for the MCP tool adapter.
    """
    name: str
    type: Literal["mcp"]
    function: str                # Identifier of the MCP function/task
    endpoint: HttpUrl            # URL of the MCP server
    headers: Dict[str, str] = {} # Optional HTTP headers for auth, etc.


class MCPToolFactory(BaseFactory):
    """
    Factory for creating MCPToolAdapter instances from config.
    """

    def accepts(self, cfg: Dict[str, Any]) -> bool:
        # This factory handles configs where type == "mcp"
        return cfg.get("type") == "mcp"

    def create(self, cfg: Dict[str, Any]) -> MCPToolAdapter:
        # 1) Validate config against schema
        try:
            data = MCPToolConfig(**cfg)
        except ValidationError as ve:
            raise PluginConfigurationError("Invalid MCP tool config", cfg) from ve

        # 2) Instantiate the adapter
        try:
            adapter = MCPToolAdapter(
                tool_name=data.name,
                mcp_function=data.function,
                endpoint=str(data.endpoint),
                headers=data.headers,
            )
        except Exception as e:
            raise PluginConfigurationError(f"Failed to create MCPToolAdapter: {e}", cfg) from e

        return adapter
