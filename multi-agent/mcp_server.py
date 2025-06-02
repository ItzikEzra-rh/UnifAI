from mcp.server.fastmcp import FastMCP

# Initialize the MCP server with a name and configuration
mcp = FastMCP(
    name="Greeting Server",
    host="0.0.0.0",
    port=8004
)


# Define a tool using the @mcp.tool() decorator
@mcp.tool()
def addition(x: int, y: int):
    """
    Returns a the addition of two numbers
    """
    return x + y


@mcp.tool()
def division(x: int, y: int):
    """
    Returns a the division of two numbers
    """
    return x / y


@mcp.tool()
def substitute(x: int, y: int):
    """
    Returns a the substitution of two numbers
    """
    return x - y


# Run the server using SSE transport
if __name__ == "__main__":
    mcp.run(transport="sse")
