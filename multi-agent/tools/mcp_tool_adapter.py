from tools.base_tool import BaseTool


class MCPToolAdapter(BaseTool):
    """
    Wraps an MCP tool-style function into a standard tool interface.
    """

    def __init__(self, tool_name: str, mcp_function):
        self._tool_name = tool_name
        self._mcp_function = mcp_function  # This is a callable

    def name(self) -> str:
        return self._tool_name

    def invoke(self, input_data: dict) -> dict:
        try:
            result = self._mcp_function(input_data)
            return {"result": result}
        except Exception as e:
            return {"error": str(e)}
