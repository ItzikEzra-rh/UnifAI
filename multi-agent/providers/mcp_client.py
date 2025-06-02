from typing import Dict, List, Any
from mcp import ClientSession
from mcp.client.sse import sse_client
from mcp.types import Tool, CallToolResult, CreateMessageRequestParams, CreateMessageResult
import mcp.types as types
from typing import Optional
import asyncio
import time


class McpClientError(Exception):
    """Base exception for MCP client operations"""
    pass


class McpToolError(McpClientError):
    """Exception for tool-related errors"""
    pass


class McpConnectionError(McpClientError):
    """Exception for connection-related errors"""
    pass


class McpHealthCheckError(McpConnectionError):
    """Exception for health check failures"""
    pass


class McpServerClient:
    """
    A robust client for connecting to MCP servers via SSE or stdio transports.
    Follows the official MCP Python SDK patterns with enhanced connection health checking.
    """

    def __init__(self, sse_endpoint, health_check_timeout: float = 5.0, max_reconnect_attempts: int = 3):
        self.sse_endpoint = sse_endpoint
        self.health_check_timeout = health_check_timeout
        self.max_reconnect_attempts = max_reconnect_attempts

        self._tools_cache: Optional[List[Tool]] = None
        self._session: Optional[ClientSession] = None
        self._read_stream = None
        self._write_stream = None
        self._transport_context = None
        self._is_connected = False
        self._last_health_check: Optional[float] = None
        self._health_check_interval = 30.0  # Check health every 30 seconds when needed

    @property
    def is_connected(self) -> bool:
        """Check if client is currently connected (basic state check)"""
        return self._is_connected and self._session is not None

    async def is_actually_connected(self) -> bool:
        """
        Perform an actual health check to verify the connection is alive.
        This does a lightweight operation to test the connection.

        Returns:
            bool: True if connection is verified working, False otherwise
        """
        if not self.is_connected:
            return False

        # Check if we've done a recent health check
        current_time = time.time()
        if (self._last_health_check and
                current_time - self._last_health_check < self._health_check_interval):
            return True

        try:
            # Perform a lightweight health check by listing tools with a timeout
            await asyncio.wait_for(
                self._session.list_tools(),
                timeout=self.health_check_timeout
            )
            self._last_health_check = current_time
            return True

        except asyncio.TimeoutError:
            print(f"Health check timed out after {self.health_check_timeout}s")
            await self._mark_disconnected()
            return False
        except Exception as e:
            print(f"Health check failed: {e}")
            await self._mark_disconnected()
            return False

    async def _mark_disconnected(self) -> None:
        """Mark the connection as disconnected and clear cache"""
        self._is_connected = False
        self._last_health_check = None
        self._tools_cache = None

    async def ensure_connected(self, force_health_check: bool = False) -> None:
        """
        Ensure the client is connected to the MCP server with optional health check.

        Args:
            force_health_check: If True, always perform a health check even if recently done

        Raises:
            McpConnectionError: If connection fails
        """
        # If we're not connected at all, connect
        if not self.is_connected:
            await self.connect()
            return

        # If force check or no recent health check, verify connection is alive
        if force_health_check or not await self.is_actually_connected():
            print("Connection health check failed, attempting to reconnect...")
            await self._reconnect_with_retry()

    async def _reconnect_with_retry(self) -> None:
        """Attempt to reconnect with retry logic"""
        for attempt in range(self.max_reconnect_attempts):
            try:
                print(f"Reconnection attempt {attempt + 1}/{self.max_reconnect_attempts}")

                # Clean disconnect first
                await self._cleanup_connection()

                # Wait a bit before reconnecting
                if attempt > 0:
                    wait_time = min(2 ** (attempt - 1), 10)  # Cap at 10 seconds
                    print(f"Waiting {wait_time}s before reconnect attempt...")
                    await asyncio.sleep(wait_time)

                await self.connect()
                print(f"Successfully reconnected on attempt {attempt + 1}")
                return

            except Exception as e:
                print(f"Reconnection attempt {attempt + 1} failed: {e}")
                if attempt == self.max_reconnect_attempts - 1:
                    raise McpConnectionError(f"Failed to reconnect after {self.max_reconnect_attempts} attempts: {e}")
                # Continue to next attempt

    async def _create_sampling_callback(
            self, message: CreateMessageRequestParams
    ) -> CreateMessageResult:
        """Default sampling callback for the session"""
        return CreateMessageResult(
            role="assistant",
            content=types.TextContent(
                type="text",
                text="Default response from MCP client",
            ),
            model="unknown",
            stopReason="endTurn",
        )

    async def connect(self) -> None:
        """Establish connection to the MCP server"""
        if self._is_connected:
            print("Client is already connected")
            return

        # Ensure we start with a clean state
        await self._cleanup_connection()

        try:
            if self.sse_endpoint:
                # SSE transport
                server_url = str(self.sse_endpoint)
                print(f"Connecting to MCP server via SSE at {server_url}")

                # Create the transport context
                self._transport_context = sse_client(url=server_url)

                # Enter the context and get streams
                try:
                    self._read_stream, self._write_stream = await self._transport_context.__aenter__()
                except Exception as e:
                    # If entering context fails, make sure we don't leave it hanging
                    self._transport_context = None
                    raise

            else:
                raise McpConnectionError("No valid transport configuration found")

            # Create session with proper callback
            self._session = ClientSession(
                self._read_stream,
                self._write_stream,
                sampling_callback=self._create_sampling_callback
            )

            # Initialize the session
            try:
                await self._session.__aenter__()
                await self._session.initialize()
            except Exception as e:
                # If session initialization fails, clean up
                self._session = None
                raise

            self._is_connected = True
            self._last_health_check = time.time()
            print("Successfully connected to MCP server")

        except Exception as e:
            print(f"Failed to connect to MCP server: {e}")
            # Ensure cleanup happens even if connection failed
            await self._cleanup_connection()
            raise McpConnectionError(f"Connection failed: {e}") from e

    async def _cleanup_connection(self) -> None:
        """Clean up connection resources"""
        # Mark as disconnected first to prevent new operations
        self._is_connected = False
        self._last_health_check = None
        self._tools_cache = None

        # Close session first
        if self._session:
            try:
                await self._session.__aexit__(None, None, None)
            except Exception as e:
                print(f"Error closing session: {e}")
            finally:
                self._session = None

        # Clear streams before closing transport
        self._read_stream = None
        self._write_stream = None

        # Close transport context with proper error handling
        if self._transport_context:
            try:
                # For SSE client, we need to handle the generator cleanup carefully
                await self._transport_context.__aexit__(None, None, None)
            except (RuntimeError, GeneratorExit, Exception) as e:
                # These are expected during cleanup, especially with SSE transport
                print(f"Transport cleanup completed with expected error: {type(e).__name__}: {e}")
            finally:
                self._transport_context = None

    async def disconnect(self) -> None:
        """Disconnect from the MCP server"""
        if not self._is_connected:
            return

        print("Disconnecting from MCP server...")
        try:
            await self._cleanup_connection()
            print("Successfully disconnected from MCP server")
        except Exception as e:
            print(f"Error during disconnect (this may be normal): {e}")
            # Ensure state is cleaned up even if cleanup fails
            self._is_connected = False
            self._last_health_check = None
            self._tools_cache = None
            self._session = None
            self._transport_context = None
            self._read_stream = None
            self._write_stream = None

    async def get_tools(self, refresh: bool = False, health_check: bool = True) -> List[Tool]:
        """
        Get available tools from the server

        Args:
            refresh: If True, bypass cache and fetch fresh tool list
            health_check: If True, perform health check before operation

        Returns:
            List of available tools
        """
        await self.ensure_connected(force_health_check=health_check)

        if not refresh and self._tools_cache is not None:
            return self._tools_cache

        try:
            # Use the official SDK method
            tool_list = await self._session.list_tools()
            self._tools_cache = tool_list.tools
            self._last_health_check = time.time()  # Update health check time

            print(f"Retrieved {len(self._tools_cache)} tools from server")
            return self._tools_cache

        except Exception as e:
            print(f"Failed to retrieve tools: {e}")
            await self._mark_disconnected()
            raise McpToolError(f"Failed to get tools: {e}") from e

    async def get_resources(self, refresh: bool = False, health_check: bool = True) -> List[Dict[str, Any]]:
        """Get available resources from the server"""
        await self.ensure_connected(force_health_check=health_check)

        try:
            resources = await self._session.list_resources()
            self._last_health_check = time.time()
            return [
                {
                    "uri": resource.uri,
                    "name": resource.name,
                    "description": resource.description or "No description available",
                    "mimeType": getattr(resource, 'mimeType', None)
                }
                for resource in resources.resources
            ]
        except Exception as e:
            print(f"Failed to retrieve resources: {e}")
            await self._mark_disconnected()
            raise McpToolError(f"Failed to get resources: {e}") from e

    async def read_resource(self, uri: str, health_check: bool = True) -> tuple[str, Optional[str]]:
        """Read a specific resource by URI"""
        await self.ensure_connected(force_health_check=health_check)

        try:
            content, mime_type = await self._session.read_resource(uri)
            self._last_health_check = time.time()
            return content, mime_type
        except Exception as e:
            print(f"Failed to read resource {uri}: {e}")
            await self._mark_disconnected()
            raise McpToolError(f"Failed to read resource: {e}") from e

    async def get_tool_names(self, refresh: bool = False, health_check: bool = True) -> List[str]:
        """Get list of available tool names"""
        tools = await self.get_tools(refresh=refresh, health_check=health_check)
        return [tool.name for tool in tools]

    async def get_tool_by_name(self, name: str, health_check: bool = True) -> Optional[Tool]:
        """Get specific tool information by name"""
        tools = await self.get_tools(health_check=health_check)
        return next((tool for tool in tools if tool.name == name), None)

    async def has_tool(self, name: str, health_check: bool = True) -> bool:
        """Check if a specific tool is available"""
        tool = await self.get_tool_by_name(name, health_check=health_check)
        return tool is not None

    async def call_tool(
            self,
            tool_name: str,
            arguments: Dict[str, Any] = None,
            validate_args: bool = True,
            health_check: bool = True
    ) -> CallToolResult:
        """
        Call a tool on the MCP server

        Args:
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool
            validate_args: Whether to validate arguments against tool schema
            health_check: Whether to perform health check before call

        Returns:
            Tool execution result
        """
        await self.ensure_connected(force_health_check=health_check)

        arguments = arguments or {}
        # Validate tool exists
        tool = await self.get_tool_by_name(tool_name, health_check=False)  # Already checked connection
        if not tool:
            available_tools = await self.get_tool_names(health_check=False)
            raise McpToolError(
                f"Tool '{tool_name}' not found. Available tools: {available_tools}"
            )

        # Optional: Validate arguments against schema
        if validate_args and tool.inputSchema:
            try:
                required_fields = tool.inputSchema.get('required', [])
                for field in required_fields:
                    if field not in arguments:
                        raise McpToolError(
                            f"Missing required argument '{field}' for tool '{tool_name}'"
                        )
            except Exception as e:
                print(f"Argument validation failed: {e}")

        try:
            print(f"Calling tool '{tool_name}' with args: {arguments}")
            result = await self._session.call_tool(tool_name, arguments)
            self._last_health_check = time.time()
            print(f"Tool '{tool_name}' executed successfully")
            return result

        except Exception as e:
            print(f"Tool call failed: {e}")
            await self._mark_disconnected()
            raise McpToolError(f"Failed to call tool '{tool_name}': {e}") from e

    async def call_tool_safe(
            self,
            tool_name: str,
            arguments: Dict[str, Any] = None,
            health_check: bool = True
    ) -> Optional[CallToolResult]:
        """
        Safe version of call_tool that returns None on error instead of raising
        """
        try:
            return await self.call_tool(tool_name, arguments, health_check=health_check)
        except McpClientError as e:
            print(f"Tool call failed safely: {e}")
            return None

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a comprehensive health check and return status information

        Returns:
            Dict containing health check results
        """
        result = {
            "is_connected": self.is_connected,
            "last_health_check": self._last_health_check,
            "health_check_age": None,
            "connection_alive": False,
            "tools_available": 0,
            "error": None
        }

        if self._last_health_check:
            result["health_check_age"] = time.time() - self._last_health_check

        try:
            result["connection_alive"] = await self.is_actually_connected()
            if result["connection_alive"]:
                tools = await self.get_tools(health_check=False)
                result["tools_available"] = len(tools)
        except Exception as e:
            result["error"] = str(e)

        return result

    def print_tools(self) -> None:
        """Print formatted tool information"""
        if not self._tools_cache:
            print("No tools cached. Call get_tools() first.")
            return

        print(f"\n=== Available Tools ({len(self._tools_cache)}) ===")
        for tool in self._tools_cache:
            print(f"\nTool: {tool.name}")
            print(f"Description: {tool.description}")
            if tool.input_schema:
                print(f"Schema: {tool.input_schema}")
            print("-" * 50)

    async def __aenter__(self):
        """Context manager entry"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        try:
            await self.disconnect()
        except Exception as e:
            # Don't raise cleanup errors in context manager exit
            print(f"Error during context manager cleanup: {e}")
            return False  # Don't suppress the original exception if there was one