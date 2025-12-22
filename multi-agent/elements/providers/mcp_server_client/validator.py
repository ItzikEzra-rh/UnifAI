"""
elements/providers/mcp_server_client/validator.py

Validator for MCP Provider - checks endpoint reachability using McpServerClient.
"""

import anyio
from concurrent.futures import CancelledError
from typing import List

from global_utils.utils.async_bridge import get_async_bridge
from elements.common.validator import (
    BaseElementValidator,
    ValidatorReport,
    ValidationContext,
    ValidationMessage,
    ValidationCode,
)
from elements.providers.mcp_server_client.config import McpProviderConfig
from elements.providers.mcp_server_client.mcp_server_client import McpServerClient


class McpProviderValidator(BaseElementValidator):
    """
    Validates MCP Provider configuration.
    
    Checks:
    - MCP server connectivity
    - Ability to list tools from the server
    """

    def validate(
        self,
        config: McpProviderConfig,
        context: ValidationContext,
    ) -> ValidatorReport:
        """
        Validate MCP provider config.
        
        Synchronous method - runs async checks internally using AsyncBridge.
        Returns ValidatorReport (service adds metadata).
        
        Note: We catch RuntimeError here (not inside async code) because the MCP
        library's streamablehttp_client has a bug that corrupts anyio's cancel
        scope stack during connection failures. This causes a RuntimeError to be
        raised during the AsyncBridge's portal cleanup - AFTER the async code
        has finished executing. The error cannot be caught inside the async
        function; it must be caught here at the sync boundary.
        """
        messages: List[ValidationMessage] = []

        try:
            with get_async_bridge() as bridge:
                bridge.run(self._check_connection(config, context, messages))
        except (CancelledError, TimeoutError) as e:
            messages.append(self._error(
                ValidationCode.NETWORK_TIMEOUT.value,
                str(e),
                field="sse_endpoint",
            ))
        except RuntimeError as e:
            # MCP library cancel scope corruption on connection failure
            messages.append(self._error(
                ValidationCode.ENDPOINT_UNREACHABLE.value,
                f"Connection failed: {e}",
                field="sse_endpoint",
            ))

        return self._build_report(messages=messages)

    async def _check_connection(
        self,
        config: McpProviderConfig,
        context: ValidationContext,
        messages: List[ValidationMessage],
    ) -> None:
        """
        Async MCP connection check using McpServerClient.
        
        Uses anyio.fail_after INSIDE the async function for timeout control.
        """
        try:
            with anyio.fail_after(context.timeout_seconds):
                client = McpServerClient(config.sse_endpoint)
                async with client:
                    await client.tools.get_tools()
            
            # Connection successful
            messages.append(self._info(
                "CONNECTION_OK",
                f"Successfully connected to MCP server at {config.sse_endpoint}",
                field="sse_endpoint",
            ))

        except TimeoutError:
            messages.append(self._error(
                ValidationCode.NETWORK_TIMEOUT.value,
                f"Connection timed out after {context.timeout_seconds}s",
                field="sse_endpoint",
            ))
        except Exception as e:
            messages.append(self._error(
                ValidationCode.ENDPOINT_UNREACHABLE.value,
                f"Connection failed: {str(e)}",
                field="sse_endpoint",
            ))
