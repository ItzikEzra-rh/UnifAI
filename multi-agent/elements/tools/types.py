from typing import Union, Annotated
from pydantic import Field
from elements.tools.ssh_exec.config import SshExecToolConfig
from elements.tools.mcp_proxy.config import McpProxyToolConfig

# Union type for backward compatibility with blueprints
ToolsSpec = Union[
    SshExecToolConfig,
    McpProxyToolConfig,
]
