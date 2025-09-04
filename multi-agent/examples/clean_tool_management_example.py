"""
Example demonstrating the clean tool management API.
"""
from elements.tools.common.execution import ToolExecutorManager
from elements.tools.common.base_tool import BaseTool


class MockTool(BaseTool):
    """Mock tool for demonstration."""
    
    def __init__(self, name: str):
        self.name = name
        self.description = f"Mock tool {name}"
    
    def run(self, **kwargs):
        return f"Result from {self.name} with args: {kwargs}"


def demonstrate_clean_tool_management():
    """Show the clean tool management API."""
    
    # Create executor
    executor = ToolExecutorManager()
    
    # Create some tools
    calculator = MockTool("calculator")
    weather = MockTool("weather")
    translator = MockTool("translator")
    
    print("=== Clean Tool Management API Demo ===")
    
    # Add tools using clean API
    executor.add_tool(calculator)
    executor.add_tool(weather)
    
    print(f"✅ Added tools: {executor.get_tool_names()}")
    
    # Add multiple tools at once
    executor.add_tools({
        "translator": translator
    })
    
    print(f"✅ After adding translator: {executor.get_tool_names()}")
    
    # Check if tools exist
    print(f"✅ Has calculator: {executor.has_tool('calculator')}")
    print(f"✅ Has unknown tool: {executor.has_tool('unknown')}")
    
    # Get a specific tool
    calc_tool = executor.get_tool("calculator")
    print(f"✅ Retrieved calculator tool: {calc_tool.name if calc_tool else 'None'}")
    
    # Remove a tool
    removed = executor.remove_tool("weather")
    print(f"✅ Removed weather tool: {removed}")
    print(f"✅ Tools after removal: {executor.get_tool_names()}")
    
    # Set entirely new tools (replaces all existing)
    new_tools = {
        "email": MockTool("email"),
        "calendar": MockTool("calendar")
    }
    executor.set_tools(new_tools)
    print(f"✅ After setting new tools: {executor.get_tool_names()}")
    
    print("\n=== Tool Management with ToolCapableMixin ===")
    
    # This would be used in ToolCapableMixin like:
    print("# In ToolCapableMixin initialization:")
    print("self._executor.set_tools(self._tools)  # Clean API!")
    print("")
    print("# Dynamic tool management:")
    print("self.add_tool(new_tool)     # Adds to both registries")
    print("self.remove_tool('old')     # Removes from both registries")
    print("self.has_tool('calculator') # Check availability")


if __name__ == "__main__":
    demonstrate_clean_tool_management()

