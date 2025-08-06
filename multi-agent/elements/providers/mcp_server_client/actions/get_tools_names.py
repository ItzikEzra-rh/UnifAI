from typing import List
from pydantic import BaseModel, HttpUrl
from elements.common.actions import BaseAction
from elements.common.action_models import BaseActionInput, BaseActionOutput, ActionType
from ..mcp_server_client import McpServerClient


# Input/Output models for this action
class GetToolsNamesInput(BaseActionInput):
    """Input for MCP tools discovery"""
    sse_endpoint: HttpUrl


class GetToolsNamesOutput(BaseActionOutput):
    """Output for MCP tools discovery"""
    tool_names: List[str] = []
    total_count: int = 0


class GetToolsNamesAction(BaseAction):
    """
    Discovers available tool names from MCP server.
    
    Single Responsibility: Only discovers and returns tool names
    """
    
    name = "get_tools_names"
    description = "Retrieve the list of available tool names from the MCP server"
    action_type = ActionType.DISCOVERY
    input_schema = GetToolsNamesInput
    output_schema = GetToolsNamesOutput
    
    async def execute(self, input_data: GetToolsNamesInput) -> GetToolsNamesOutput:
        """
        Execute tools discovery asynchronously.
        
        Args:
            input_data: Validated discovery input
            
        Returns:
            Discovery result with tool names and count
        """
        try:
            # Create client and discover tools
            client = McpServerClient(input_data.sse_endpoint)
            
            async with client:
                tools = await client.tools.get_tools()
                tool_names = [tool.name for tool in tools]
            
            return GetToolsNamesOutput(
                success=True,
                message=f"Found {len(tool_names)} tools",
                tool_names=tool_names,
                total_count=len(tool_names)
            )
            
        except Exception as e:
            return GetToolsNamesOutput(
                success=False,
                message=f"Failed to retrieve tools: {str(e)}",
                tool_names=[],
                total_count=0
            )