"""
Example showing the clean model-based API for monitoring and status.

This demonstrates the type-safe, structured approach to returning
monitoring data instead of raw dictionaries.
"""
import asyncio
from elements.tools.common.execution import (
    ToolExecutorManager,
    ExecutorMetrics,
    ExecutorHealth, 
    CircuitBreakerReport,
    CircuitBreakerStatus,
    CircuitBreakerState,
    create_robust_executor
)
from elements.tools.common.base_tool import BaseTool


class ExampleTool(BaseTool):
    """Example tool for demonstration."""
    
    def __init__(self, name: str, should_fail: bool = False):
        super().__init__(name)
        self.should_fail = should_fail
    
    async def arun(self, **kwargs) -> str:
        if self.should_fail:
            raise Exception(f"Deliberate failure from {self.name}")
        return f"Success from {self.name}"


async def demonstrate_clean_models():
    """Demonstrate the clean model-based monitoring API."""
    print("🚀 Clean Model-Based Monitoring API Demo")
    print("=" * 50)
    
    # Create executor with circuit breaker
    executor = create_robust_executor(
        max_concurrent=2,
        enable_circuit_breaker=True
    )
    
    # Add some tools
    tools = [
        ExampleTool("reliable_tool", should_fail=False),
        ExampleTool("unreliable_tool", should_fail=True)
    ]
    
    for tool in tools:
        executor.add_tool(tool)
    
    print("\n📊 Initial Metrics")
    print("-" * 20)
    metrics: ExecutorMetrics = executor.metrics
    print(f"Type: {type(metrics).__name__}")
    print(f"Executions: {metrics.total_executions}")
    print(f"Success rate: {metrics.success_rate:.1f}%")
    print(f"Tools registered: {metrics.tools_registered}")
    print(f"Is healthy: {metrics.is_healthy}")
    print(f"Strategies: {metrics.strategies}")
    
    print("\n🏥 Health Status")
    print("-" * 20)
    health: ExecutorHealth = executor.get_health()
    print(f"Type: {type(health).__name__}")
    print(f"Status: {health.status}")
    print(f"Is healthy: {health.is_healthy}")
    print(f"Features enabled: {health.features_enabled}")
    
    print("\n⚡ Circuit Breaker Status")
    print("-" * 20)
    cb_report: CircuitBreakerReport = executor.get_circuit_breaker_status()
    print(f"Type: {type(cb_report).__name__}")
    print(f"Enabled: {cb_report.enabled}")
    print(f"Overall health: {cb_report.overall_health}")
    print(f"Healthy tools: {cb_report.healthy_tools}")
    print(f"Unhealthy tools: {cb_report.unhealthy_tools}")
    
    # Show individual tool status
    for tool_name, status in cb_report.tool_statuses.items():
        print(f"  {tool_name}: {status.state.value} (can_execute: {status.can_execute})")
    
    print("\n🔍 Type Safety Benefits")
    print("-" * 20)
    print("✅ IDE autocomplete for all properties")
    print("✅ Type checking catches errors at development time")
    print("✅ Clear, structured data instead of nested dictionaries")
    print("✅ Built-in helper methods like .is_healthy, .overall_health")
    print("✅ Proper string representations for logging")
    
    print(f"\n📝 String Representations")
    print("-" * 20)
    print(f"Metrics: {metrics}")
    print(f"Health: {health}")
    print(f"Circuit Breaker: {cb_report}")
    
    print("\n🎯 Accessing Specific Properties")
    print("-" * 20)
    
    # Type-safe property access
    print(f"Error rate: {metrics.error_rate}%")
    print(f"Tools with features: {len([name for name in metrics.tool_names])}")
    print(f"Strategies available: {list(metrics.strategies.keys())}")
    
    # Circuit breaker insights
    if cb_report.enabled:
        for tool_name, status in cb_report.tool_statuses.items():
            print(f"{tool_name} circuit breaker:")
            print(f"  State: {status.state.value}")
            print(f"  Failures: {status.failure_count}")
            print(f"  Can execute: {status.can_execute}")
            print(f"  Is healthy: {status.is_healthy}")


if __name__ == "__main__":
    asyncio.run(demonstrate_clean_models())

