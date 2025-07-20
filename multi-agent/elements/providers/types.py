from typing import Union, Annotated
from pydantic import Field
from elements.providers.mcp_server_client.config import McpProviderConfig

# Union type for backward compatibility with blueprints
ProviderSpec = Union[
    McpProviderConfig,
]
