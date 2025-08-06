import asyncio
import time
from pydantic import BaseModel, HttpUrl
from elements.common.actions import BaseAction
from elements.common.action_models import BaseActionInput, BaseActionOutput, ActionType
from ..mcp_server_client import McpServerClient


# Input/Output models for this action
class ValidateConnectionInput(BaseActionInput):
    """Input for MCP connection validation"""
    sse_endpoint: HttpUrl


class ValidateConnectionOutput(BaseActionOutput):
    """Output for MCP connection validation"""
    is_reachable: bool = False
    response_time_ms: float = 0.0


class ValidateConnectionAction(BaseAction):
    """
    Validates MCP server connection.
    
    Single Responsibility: Only validates connection reachability
    """
    
    name = "validate_connection"
    description = "Validate that the MCP server endpoint is reachable and responding"
    action_type = ActionType.VALIDATION
    input_schema = ValidateConnectionInput
    output_schema = ValidateConnectionOutput
    
    async def execute(self, input_data: ValidateConnectionInput) -> ValidateConnectionOutput:
        """
        Execute connection validation asynchronously.
        
        Args:
            input_data: Validated connection input
            
        Returns:
            Validation result with connection status and timing
        """
        start_time = time.time()
        
        try:
            # Create client and test connection
            client = McpServerClient(input_data.sse_endpoint)
            
            async with client:
                # Test connection by listing tools with timeout
                await asyncio.wait_for(client.tools.get_tools(), timeout=10.0)
            
            response_time = (time.time() - start_time) * 1000
            
            return ValidateConnectionOutput(
                success=True,
                message="Connection successful",
                is_reachable=True,
                response_time_ms=response_time
            )
            
        except asyncio.TimeoutError:
            return ValidateConnectionOutput(
                success=False,
                message="Connection timeout - server may be unreachable",
                is_reachable=False,
                response_time_ms=(time.time() - start_time) * 1000
            )
        except Exception as e:
            return ValidateConnectionOutput(
                success=False,
                message=f"Connection failed: {str(e)}",
                is_reachable=False,
                response_time_ms=(time.time() - start_time) * 1000
            )