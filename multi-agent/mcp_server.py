from mcp.server.fastmcp import FastMCP

# Initialize the MCP server with a name and configuration
mcp = FastMCP(
    name="Greeting Server",
    host="0.0.0.0",
    port=8004
)


# Define a tool using the @mcp.tool() decorator
@mcp.tool()
def greet_user(name: str):
    """
    Returns a personalized greeting message.
    """
    return f"Hello, {name}! Welcome to the MCP server.", "odai"


# Run the server using SSE transport
if __name__ == "__main__":
    mcp.run(transport="sse")
