"""
SSE (Server-Sent Events) transport manager for MCP connections.

Uses the ``mcp.client.sse.sse_client`` to open a unidirectional SSE
stream to the MCP server.
"""

from typing import Any, Tuple

from mcp.client.sse import sse_client

from .base_transport import BaseTransportManager
from .enums import McpTransportType


class SseTransportManager(BaseTransportManager):
    """
    MCP transport over Server-Sent Events (SSE).

    The SSE transport does not support custom HTTP headers.
    Authentication must be handled at a different layer
    (e.g. query parameters or proxy).
    """

    @property
    def transport_type(self) -> McpTransportType:
        return McpTransportType.SSE

    @property
    def _transport_label(self) -> str:
        return "SSE"

    def _create_transport_context(self) -> Any:
        return sse_client(url=self.endpoint)

    async def _enter_transport_context(self, ctx: Any) -> Tuple:
        read_stream, write_stream = await ctx.__aenter__()
        return read_stream, write_stream
