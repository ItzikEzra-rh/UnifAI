from typing import Optional, Type, Any, Dict
from pydantic import BaseModel
from global_utils.utils.util import json_schema_model, run_async
from providers.mcp.mcp_server_client import McpServerClient
from .base_tool import BaseTool


class McpProxyToolError(Exception):
    """Exception for MCP proxy tool errors"""
    pass


class McpProxyTool(BaseTool):
    """
    A proxy tool that forwards calls to MCP server tools through McpServerClient.
    Inherits from BaseTool (LangChain-compatible). Dynamically adapts to the MCP tool's schema.
    """

    def __init__(
            self,
            mcp_tool_name: str,
            mcp_client: McpServerClient,
            custom_name: Optional[str] = None,
            custom_description: Optional[str] = None
    ):
        self.mcp_tool_name = mcp_tool_name
        self.mcp_client = mcp_client
        self._tool_info = None
        self._schema_initialized = False

        # Pass placeholder values up to BaseTool. We will replace them once we fetch real info.
        super().__init__(
            name=custom_name or mcp_tool_name,
            description=custom_description or f"MCP proxy for {mcp_tool_name}",
            args_schema=None
        )

        # Kick off an initial fetch of schema/info in the background.
        run_async(self._ensure_tool_info())

    async def _ensure_tool_info(self) -> None:
        """
        Make sure we've fetched the remote tool's metadata (description + inputSchema).
        Uses `async with self.mcp_client:` so that connect/disconnect happen automatically.
        """
        if self._tool_info is None:
            # Entering this block calls `await self.mcp_client.connect()`.
            async with self.mcp_client.clone() as client:
                # Fetch the tool info by name
                tool_info = await client.get_tool_by_name(self.mcp_tool_name)

            # Exiting the block calls `await self.mcp_client.disconnect()`
            if not tool_info:
                # If the server reported no such tool, list all available for error message
                async with self.mcp_client.clone() as client:
                    available = await client.get_tools()
                raise McpProxyToolError(
                    f"MCP tool '{self.mcp_tool_name}' not found. Available tools: {available}"
                )

            # Store the fetched info locally
            self._tool_info = tool_info
            # Update our BaseTool fields with real data
            self.description = tool_info.description
            self.args_schema = tool_info.inputSchema
            self._schema_initialized = True

    def run(self, *args: Any, **kwargs: Any) -> Any:
        """
        Synchronous wrapper so that BaseTool.run() can call into our async code.
        """
        try:
            return run_async(self.arun(*args, **kwargs))
        except Exception as e:
            raise McpProxyToolError(f"Synchronous execution failed for '{self.mcp_tool_name}': {e}")

    async def arun(self, *args: Any, **kwargs: Any) -> Any:
        """
        Asynchronous execution path. Wraps each MCP call in `async with self.mcp_client:`
        so that:
          - entering the block automatically connects if needed
          - exiting automatically disconnects
        """
        # Ensure we have schema and description before calling
        if not self._schema_initialized:
            await self._ensure_tool_info()

        # Validate / prepare arguments according to the fetched JSON schema
        mcp_args = self._prepare_arguments(kwargs)

        # Enter MCP context (connect if not already connected), then call the tool
        async with self.mcp_client.clone() as client:
            # The client is guaranteed to be connected now
            try:
                result = await client.call_tool(self.mcp_tool_name, mcp_args)
            except Exception as e:
                raise McpProxyToolError(f"Failed to call '{self.mcp_tool_name}': {e}")

        # Exiting the `async with` block automatically disconnects
        return self._extract_result_content(result)

    def _prepare_arguments(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate & prune arguments against the dynamic Pydantic model generated from JSON schema.
        If schema is missing or validation fails, fall back to raw kwargs.
        """
        if not kwargs or not self.args_schema:
            return kwargs or {}

        try:
            model_cls = self.get_args_schema_model()
            validated = model_cls(**kwargs)
            return {k: v for k, v in validated.model_dump().items() if v is not None}
        except Exception:
            # If validation errors, just pass through
            return kwargs

    def _extract_result_content(self, result) -> Any:
        """
        Take whatever `CallToolResult` returned and pick out the most relevant piece.
        Typically MCP returns a `.content` list of TextContent or DataContent objects.
        """
        try:
            if hasattr(result, "content") and result.content:
                # If it's a list, pick the first element
                if isinstance(result.content, list) and len(result.content) > 0:
                    first = result.content[0]
                    # If this content object has `.text`, return it
                    if hasattr(first, "text"):
                        return first.text
                    # If it has `.data`, return that
                    if hasattr(first, "data"):
                        return first.data
                    # Otherwise stringify whatever this element is
                    return str(first)
                # If content is a single‐item (not list), just str() it
                return str(result.content)

            # Fallback to printing the entire result object
            return str(result)
        except Exception:
            return str(result)

    def get_args_schema_json(self) -> Dict[str, Any]:
        """
        Return the raw JSON schema that MCP told us. LangChain’s BaseTool may use this to display
        the schema or generate prompts.
        """
        return self.args_schema

    def get_args_schema_model(self) -> Optional[Type[BaseModel]]:
        """
        Dynamically build a Pydantic model from the MCP JSON schema. This allows us to
        type-check and validate arguments before sending them upstream.
        """
        if not self.args_schema:
            return None

        return json_schema_model(self.args_schema, self.name)

    async def refresh_schema(self) -> None:
        """
        Re-fetch the tool’s JSON schema & description. Useful if the remote tool definition changed.
        """
        self._tool_info = None
        self._schema_initialized = False
        self.args_schema = None
        await self._ensure_tool_info()

    async def health_check(self) -> bool:
        """
        Quick way to verify that:
          1) we can connect to MCP
          2) the remote tool still exists & its schema is retrievable
        """
        try:
            # Enter the context (connect), then check for tool info
            async with self.mcp_client.clone() as client:
                info = await client.get_tool_by_name(self.mcp_tool_name)
            return info is not None
        except Exception:
            return False

    def __str__(self) -> str:
        return f"McpProxyTool(name='{self.name}', mcp_tool='{self.mcp_tool_name}')"

    def __repr__(self) -> str:
        desc = (self.description[:50] + "...") if self.description else "No description"
        return (
            f"McpProxyTool(name='{self.name}', mcp_tool_name='{self.mcp_tool_name}', "
            f"description='{desc}', connected={self.mcp_client.is_connected})"
        )
