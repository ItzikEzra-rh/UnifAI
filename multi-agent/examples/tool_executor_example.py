"""
Example of using ToolExecutorManager directly.

This example demonstrates various features of the tool execution framework:
- Single tool execution
- Batch execution with different strategies
- Error handling policies
- Monitoring and metrics
- Hooks for extensibility
"""
import asyncio
import logging
from typing import Dict, Any

from elements.tools.common.execution import (
    ToolExecutorManager,
    ExecutionMode,
    RetryPolicy,
    FallbackPolicy,
    CompositeErrorHandler,
    create_executor,
    create_robust_executor
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Example tool implementations
class MockTool:
    """Mock tool for demonstration purposes."""
    
    def __init__(self, name: str, success_rate: float = 1.0, delay: float = 0.1):
        self.name = name
        self.description = f"Mock tool {name}"
        self.success_rate = success_rate
        self.delay = delay
        self.args_schema = None
    
    async def arun(self, **kwargs) -> str:
        """Async execution."""
        await asyncio.sleep(self.delay)
        
        # Simulate random failures
        import random
        if random.random() > self.success_rate:
            raise Exception(f"Mock failure in {self.name}")
        
        return f"Result from {self.name} with args: {kwargs}"
    
    def run(self, **kwargs) -> str:
        """Sync execution."""
        import time
        time.sleep(self.delay)
        
        # Simulate random failures
        import random
        if random.random() > self.success_rate:
            raise Exception(f"Mock failure in {self.name}")
        
        return f"Result from {self.name} with args: {kwargs}"


class SlowTool(MockTool):
    """Tool that takes a long time to execute."""
    
    def __init__(self, name: str):
        super().__init__(name, success_rate=1.0, delay=2.0)


class UnreliableTool(MockTool):
    """Tool that fails frequently."""
    
    def __init__(self, name: str):
        super().__init__(name, success_rate=0.3, delay=0.1)


async def demonstrate_basic_execution():
    """Demonstrate basic tool execution."""
    print("\n=== Basic Execution Demo ===")
    
    # Create executor
    executor = ToolExecutorManager()
    
    # Create tools
    fast_tool = MockTool("fast_tool", success_rate=1.0, delay=0.1)
    
    # Single execution
    print("Executing single tool...")
    result = await executor.execute_async(
        tool=fast_tool,
        args={"message": "hello"},
        timeout=5.0
    )
    
    print(f"Result: {result}")
    print(f"Success: {result.success}")
    print(f"Execution time: {result.execution_time:.3f}s")


async def demonstrate_batch_execution():
    """Demonstrate batch execution with different strategies."""
    print("\n=== Batch Execution Demo ===")
    
    executor = ToolExecutorManager(max_concurrent=3)
    
    # Create multiple tools
    tools = [
        (MockTool(f"tool_{i}", delay=0.2), {"index": i})
        for i in range(5)
    ]
    
    # Sequential execution
    print("Sequential execution...")
    seq_result = await executor.execute_batch_async(
        tools=tools,
        mode=ExecutionMode.SEQUENTIAL
    )
    print(f"Sequential: {seq_result}")
    
    # Parallel execution
    print("Parallel execution...")
    par_result = await executor.execute_batch_async(
        tools=tools,
        mode=ExecutionMode.PARALLEL
    )
    print(f"Parallel: {par_result}")
    
    # Concurrent limited execution
    print("Concurrent limited execution...")
    conc_result = await executor.execute_batch_async(
        tools=tools,
        mode=ExecutionMode.CONCURRENT_LIMITED
    )
    print(f"Concurrent Limited: {conc_result}")


async def demonstrate_error_handling():
    """Demonstrate error handling policies."""
    print("\n=== Error Handling Demo ===")
    
    # Create executor with retry policy
    retry_executor = ToolExecutorManager(
        error_handler=RetryPolicy(max_retries=3, initial_delay=0.1)
    )
    
    # Create unreliable tool
    unreliable_tool = UnreliableTool("unreliable")
    
    print("Testing with retry policy...")
    result = await retry_executor.execute_async(
        tool=unreliable_tool,
        args={"test": "retry"}
    )
    
    print(f"Retry result: {result}")
    print(f"Handled error: {result.metadata.get('handled_error')}")


async def demonstrate_fallback_policy():
    """Demonstrate fallback error handling."""
    print("\n=== Fallback Policy Demo ===")
    
    # Create fallback tools
    primary_tool = UnreliableTool("primary")
    fallback1 = MockTool("fallback1", success_rate=0.8)
    fallback2 = MockTool("fallback2", success_rate=1.0)
    
    fallback_executor = ToolExecutorManager(
        error_handler=FallbackPolicy([fallback1, fallback2])
    )
    
    print("Testing fallback policy...")
    result = await fallback_executor.execute_async(
        tool=primary_tool,
        args={"test": "fallback"}
    )
    
    print(f"Fallback result: {result}")


async def demonstrate_hooks():
    """Demonstrate execution hooks."""
    print("\n=== Hooks Demo ===")
    
    executor = ToolExecutorManager()
    
    # Add monitoring hooks
    async def pre_hook(tool, args, context):
        print(f"  🚀 Starting execution of {tool.name}")
    
    async def post_hook(result, context):
        status = "✅" if result.success else "❌"
        print(f"  {status} Finished {result.tool_name} in {result.execution_time:.3f}s")
    
    executor.add_pre_execution_hook(pre_hook)
    executor.add_post_execution_hook(post_hook)
    
    # Execute with hooks
    tools = [
        (MockTool(f"hooked_tool_{i}"), {"index": i})
        for i in range(3)
    ]
    
    batch_result = await executor.execute_batch_async(
        tools=tools,
        mode=ExecutionMode.SEQUENTIAL
    )
    
    print(f"Hooks result: {batch_result}")


async def demonstrate_metrics():
    """Demonstrate metrics and monitoring."""
    print("\n=== Metrics Demo ===")
    
    executor = ToolExecutorManager(enable_metrics=True)
    
    # Execute multiple tools to generate metrics
    tools = [
        (MockTool("success_tool", success_rate=1.0), {}),
        (UnreliableTool("fail_tool"), {}),
        (MockTool("another_success", success_rate=1.0), {}),
    ]
    
    for tool, args in tools:
        await executor.execute_async(tool, args)
    
    # Display metrics
    metrics = executor.metrics
    print(f"Execution metrics: {metrics}")
    
    # Health check
    health = await executor.health_check()
    print(f"Health check: {health}")


async def demonstrate_circuit_breaker():
    """Demonstrate circuit breaker functionality."""
    print("\n=== Circuit Breaker Demo ===")
    
    executor = ToolExecutorManager(enable_circuit_breaker=True)
    
    # Create a tool that will trigger circuit breaker
    failing_tool = UnreliableTool("circuit_test")
    
    print("Executing failing tool multiple times...")
    for i in range(10):
        result = await executor.execute_async(
            tool=failing_tool,
            args={"attempt": i}
        )
        print(f"Attempt {i+1}: {'SUCCESS' if result.success else 'FAILED'}")
        
        # Check circuit breaker status
        cb_status = executor.get_circuit_breaker_status("circuit_test")
        if cb_status.get("circuit_test", {}).get("state") == "open":
            print("🔴 Circuit breaker is OPEN!")
            break


async def demonstrate_factory_functions():
    """Demonstrate convenience factory functions."""
    print("\n=== Factory Functions Demo ===")
    
    # Simple executor with retry
    simple_executor = create_executor(
        error_retry_attempts=2,
        max_concurrent=5
    )
    
    # Robust executor with comprehensive error handling
    robust_executor = create_robust_executor(max_concurrent=3)
    
    tool = MockTool("factory_test")
    
    print("Testing simple executor...")
    simple_result = await simple_executor.execute_async(tool, {"test": "simple"})
    print(f"Simple executor result: {simple_result.success}")
    
    print("Testing robust executor...")
    robust_result = await robust_executor.execute_async(tool, {"test": "robust"})
    print(f"Robust executor result: {robust_result.success}")


async def main():
    """Run all demonstrations."""
    print("🔧 Tool Executor Manager Demonstration")
    print("======================================")
    
    try:
        await demonstrate_basic_execution()
        await demonstrate_batch_execution()
        await demonstrate_error_handling()
        await demonstrate_fallback_policy()
        await demonstrate_hooks()
        await demonstrate_metrics()
        await demonstrate_circuit_breaker()
        await demonstrate_factory_functions()
        
        print("\n✅ All demonstrations completed successfully!")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        raise


def sync_main():
    """Synchronous entry point."""
    asyncio.run(main())


if __name__ == "__main__":
    # Can be run both sync and async
    import sys
    
    if "--async" in sys.argv:
        # For testing async directly
        asyncio.run(main())
    else:
        # Normal sync execution
        sync_main()
