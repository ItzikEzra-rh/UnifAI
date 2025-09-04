"""
Example demonstrating the enhanced ToolExecutorManager with all restored features.

This example showcases:
- Error handling policies (RetryPolicy, CircuitBreakerPolicy)
- Execution hooks for monitoring
- Input validation
- Timeout handling
- Circuit breaker patterns
- Comprehensive metrics
- Clean request/response API
"""
import asyncio
import logging
from typing import Dict, Any

from elements.tools.common.execution import (
    ToolExecutorManager,
    ExecutionMode,
    RetryPolicy,
    CircuitBreakerPolicy,
    ToolExecutionRequest,
    create_robust_executor
)
from elements.tools.common.base_tool import BaseTool

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MockTool(BaseTool):
    """Mock tool for testing."""
    
    def __init__(self, name: str, should_fail: bool = False, delay: float = 0.1):
        super().__init__(name)
        self.should_fail = should_fail
        self.delay = delay
        
    async def arun(self, **kwargs) -> str:
        await asyncio.sleep(self.delay)
        if self.should_fail:
            raise Exception(f"Mock failure from {self.name}")
        return f"Success from {self.name} with args: {kwargs}"
    
    def run(self, **kwargs) -> str:
        if self.should_fail:
            raise Exception(f"Mock failure from {self.name}")
        return f"Success from {self.name} with args: {kwargs}"


async def demonstrate_error_handling():
    """Demonstrate error handling with retry policy."""
    print("\n=== Error Handling with Retry Policy ===")
    
    # Create executor with retry policy
    executor = ToolExecutorManager(
        error_handler=RetryPolicy(max_retries=2, initial_delay=0.2),
        enable_metrics=True
    )
    
    # Add tools (one that fails, one that succeeds)
    failing_tool = MockTool("failing_tool", should_fail=True)
    success_tool = MockTool("success_tool", should_fail=False)
    
    executor.add_tool(failing_tool)
    executor.add_tool(success_tool)
    
    requests = [
        ToolExecutionRequest(tool_name="failing_tool", tool_call_id="fail_1", args={"test": "data"}),
        ToolExecutionRequest(tool_name="success_tool", tool_call_id="success_1", args={"test": "data"})
    ]
    
    try:
        response = await executor.execute_requests_async(requests, ExecutionMode.PARALLEL)
        
        print("Results:")
        for tool_call_id, result in response.responses.items():
            print(f"  {tool_call_id}: {'✅' if result.success else '❌'} {result.result or result.error}")
            
    except Exception as e:
        print(f"Execution error: {e}")
    
    print(f"Metrics: {executor.metrics}")


async def demonstrate_hooks():
    """Demonstrate execution hooks for monitoring."""
    print("\n=== Execution Hooks for Monitoring ===")
    
    executor = ToolExecutorManager(enable_metrics=True)
    
    # Add monitoring hooks
    async def log_before_execution(tool, args, context):
        logger.info(f"🚀 Starting execution of {tool.name} with args: {args}")
    
    async def log_after_execution(result, context):
        status = "✅ SUCCESS" if result.success else "❌ FAILED"
        logger.info(f"🏁 {status}: {result.tool_name} took {result.execution_time:.3f}s")
    
    executor.add_pre_execution_hook(log_before_execution)
    executor.add_post_execution_hook(log_after_execution)
    
    # Add tools
    tool1 = MockTool("monitored_tool_1", delay=0.1)
    tool2 = MockTool("monitored_tool_2", delay=0.2)
    
    executor.add_tools({"monitored_tool_1": tool1, "monitored_tool_2": tool2})
    
    requests = [
        ToolExecutionRequest(tool_name="monitored_tool_1", tool_call_id="mon_1", args={"data": "test1"}),
        ToolExecutionRequest(tool_name="monitored_tool_2", tool_call_id="mon_2", args={"data": "test2"})
    ]
    
    response = await executor.execute_requests_async(requests, ExecutionMode.SEQUENTIAL)
    
    print(f"Hook execution completed. Metrics: {executor.metrics}")


async def demonstrate_circuit_breaker():
    """Demonstrate circuit breaker pattern."""
    print("\n=== Circuit Breaker Pattern ===")
    
    executor = ToolExecutorManager(
        enable_circuit_breaker=True,
        enable_metrics=True
    )
    
    # Add a tool that always fails
    unreliable_tool = MockTool("unreliable_tool", should_fail=True)
    executor.add_tool(unreliable_tool)
    
    # Try to execute multiple times to trigger circuit breaker
    for i in range(7):  # Circuit breaker typically opens after 5 failures
        request = ToolExecutionRequest(
            tool_name="unreliable_tool", 
            tool_call_id=f"cb_test_{i}", 
            args={"attempt": i}
        )
        
        response = await executor.execute_requests_async([request])
        result = response.responses[f"cb_test_{i}"]
        
        print(f"Attempt {i+1}: {'✅' if result.success else '❌'} {result.error}")
        
        # Check circuit breaker status
        cb_status = executor.get_circuit_breaker_status("unreliable_tool")
        print(f"  Circuit breaker can execute: {cb_status.get('can_execute', 'N/A')}")


async def demonstrate_execution_strategies():
    """Demonstrate different execution strategies."""
    print("\n=== Execution Strategies ===")
    
    executor = ToolExecutorManager(max_concurrent=2, enable_metrics=True)
    
    # Add tools with different delays
    tools = [MockTool(f"strategy_tool_{i}", delay=0.1) for i in range(4)]
    for tool in tools:
        executor.add_tool(tool)
    
    requests = [
        ToolExecutionRequest(tool_name=f"strategy_tool_{i}", tool_call_id=f"strat_{i}", args={"test": i})
        for i in range(4)
    ]
    
    # Test different strategies
    for mode in [ExecutionMode.SEQUENTIAL, ExecutionMode.PARALLEL, ExecutionMode.CONCURRENT_LIMITED]:
        print(f"\n--- {mode.value.title()} Execution ---")
        
        start_time = asyncio.get_event_loop().time()
        response = await executor.execute_requests_async(requests, mode)
        end_time = asyncio.get_event_loop().time()
        
        print(f"Execution time: {end_time - start_time:.3f}s")
        print(f"Success count: {sum(1 for r in response.responses.values() if r.success)}/{len(requests)}")


async def demonstrate_robust_executor():
    """Demonstrate the robust executor factory."""
    print("\n=== Robust Executor (Factory) ===")
    
    # Create robust executor with all features enabled
    executor = create_robust_executor(
        max_concurrent=2,
        default_timeout=5.0
    )
    
    # Add tools
    tools = [
        MockTool("robust_tool_1", should_fail=False, delay=0.1),
        MockTool("robust_tool_2", should_fail=True, delay=0.1),  # Will be retried
        MockTool("robust_tool_3", should_fail=False, delay=0.2)
    ]
    
    for tool in tools:
        executor.add_tool(tool)
    
    requests = [
        ToolExecutionRequest(tool_name="robust_tool_1", tool_call_id="rob_1", args={"test": "data"}),
        ToolExecutionRequest(tool_name="robust_tool_2", tool_call_id="rob_2", args={"test": "data"}),
        ToolExecutionRequest(tool_name="robust_tool_3", tool_call_id="rob_3", args={"test": "data"})
    ]
    
    response = await executor.execute_requests_async(requests, ExecutionMode.PARALLEL)
    
    print("Robust execution results:")
    for tool_call_id, result in response.responses.items():
        print(f"  {tool_call_id}: {'✅' if result.success else '❌'} {result.result or result.error}")
    
    print(f"\nComprehensive metrics:")
    metrics = executor.metrics
    for key, value in metrics.items():
        if isinstance(value, dict):
            print(f"  {key}:")
            for sub_key, sub_value in value.items():
                print(f"    {sub_key}: {sub_value}")
        else:
            print(f"  {key}: {value}")


async def main():
    """Run all examples."""
    print("🚀 Enhanced ToolExecutorManager Examples")
    print("=" * 50)
    
    await demonstrate_error_handling()
    await demonstrate_hooks()
    await demonstrate_circuit_breaker()
    await demonstrate_execution_strategies()
    await demonstrate_robust_executor()
    
    print("\n🎉 All examples completed!")


if __name__ == "__main__":
    asyncio.run(main())
