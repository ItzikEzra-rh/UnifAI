import logging
from typing import Dict, Any, Optional, List

from mcp.types import Tool, CallToolResult, CreateMessageRequestParams, CreateMessageResult, TextContent

from .transport_manager import TransportManager, McpConnectionError
from .health_checker import HealthChecker
from .tool_registry import ToolRegistry, McpToolError
from schemas.providers.base_provider import McpProviderConfig


class McpProxyToolError(Exception):
    """Any error that occurs while proxying to an MCP tool."""
    pass


class McpServerClient:
    """
    A high‐level façade that ties together:
      - TransportManager (open/close SSE + ClientSession)
      - HealthChecker   (ping logic + automatic reconnect)
      - ToolRegistry    (list/get/call tools + minimal JSON‐schema validation)

    Public interface:
      - __init__(sse_endpoint, health_timeout, health_interval)
      - async with client: …  # automatically connect/disconnect
      - get_tools(refresh=False)
      - get_tool_by_name(name)
      - call_tool(name, arguments)
      - health_check() → returns True/False
    """

    def __init__(
            self,
            sse_endpoint: str,
            health_check_timeout: float = 5.0,
            health_check_interval: float = 30.0
    ):
        self.sse_endpoint = sse_endpoint
        self._health_check_timeout = health_check_timeout
        self._health_check_interval = health_check_interval

        # 1) TransportManager: handles connect()/disconnect() of SSE + ClientSession
        self.transport = TransportManager(
            self.sse_endpoint,
            sampling_callback=self._default_sampling_callback
        )

        # 2) HealthChecker: uses transport._session.list_tools() as a ping
        self.health = HealthChecker(
            transport=self.transport,
            timeout=health_check_timeout,
            interval=health_check_interval
        )

        # 3) ToolRegistry: list/get/call tools via the same transport + health
        self.tools = ToolRegistry(
            transport=self.transport,
            health_checker=self.health
        )

    async def _default_sampling_callback(
            self, message: CreateMessageRequestParams
    ) -> CreateMessageResult:
        """
        Default fallback if MCP server ever requests a sampling callback.
        """
        return CreateMessageResult(
            role="assistant",
            content=TextContent(type="text", text="Default response"),
            model="unknown",
            stopReason="endTurn"
        )

    @property
    def is_connected(self) -> bool:
        """Shortcut to transport.is_connected."""
        return self.transport.is_connected

    async def connect(self) -> None:
        """
        Explicitly open the transport & session. Normally you only need
        to do this if you plan to call get_tools() or call_tool() immediately—
        but each of those methods will auto‐connect via health.ensure_connected().
        """
        try:
            await self.transport.connect()
        except McpConnectionError as e:
            raise McpConnectionError(f"McpServerClient.connect() failed: {e}")

    async def disconnect(self) -> None:
        """
        Explicitly disconnect the transport & session. This is also called
        automatically when you exit `async with …`.
        """
        await self.transport.disconnect()

    async def get_tools(self, refresh: bool = False) -> List[Tool]:
        """
        Return a list of all available tools (possibly cached). If `refresh=True`,
        forces a fresh fetch from the server.
        """
        try:
            return await self.tools.get_tools(refresh=refresh)
        except McpToolError as e:
            raise McpToolError(f"McpServerClient.get_tools() failed: {e}")

    async def get_tool_by_name(self, name: str) -> Optional[Tool]:
        """
        Return the Tool object for a given name, or None if not found.
        """
        try:
            return await self.tools.get_tool_by_name(name)
        except McpToolError as e:
            raise McpToolError(f"McpServerClient.get_tool_by_name() failed: {e}")

    async def call_tool(
            self,
            tool_name: str,
            arguments: Dict[str, Any]
    ) -> CallToolResult:
        """
        Proxy a call to the MCP server:
          1) Ensure connected & healthy
          2) Validate `required` fields
          3) Invoke session.call_tool(...)
          4) Return the raw CallToolResult
        Raises McpToolError if something goes wrong.
        """
        try:
            return await self.tools.call_tool(tool_name, arguments)
        except McpToolError as e:
            raise McpToolError(f"McpServerClient.call_tool('{tool_name}') failed: {e}")

    async def health_check(self) -> bool:
        """
        Trigger a health check (ping). Returns True if the connection is live, else False.
        """
        try:
            return await self.health.is_actually_connected()
        except Exception as e:
            print("McpServerClient.health_check() exception: %s", e)
            return False

    def clone(self) -> "McpServerClient":
        """
        Return a brand‐new McpServerClient with exactly the same configuration
        (same sse_endpoint, same timeouts). The returned object will have no open
        connection until you do `async with new_client:` or call `await new_client.connect()`.
        """
        return McpServerClient(
            sse_endpoint=self.sse_endpoint,
            health_check_timeout=self._health_check_timeout,
            health_check_interval=self._health_check_interval
        )

    # Support `async with client:` to connect/disconnect automatically
    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.disconnect()
