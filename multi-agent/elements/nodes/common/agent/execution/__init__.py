"""
Agent execution control system.

This module provides fine-grained control over agent execution with different
modes and validation capabilities. Includes:

- AgentIterator: Step-by-step execution control with multiple modes
- AgentActionExecutor: Bridge between agent actions and tool system
- ToolValidator: Policy enforcement and permission checking
- ExecutionMode: Different execution patterns (auto, manual, guided)

Key Components:
- ExecutionMode: AUTO (automatic), MANUAL (user control), GUIDED (confirmation)
- AgentIterator: Main execution controller with streaming support
- AgentActionExecutor: Executes actions using existing ToolCapableMixin
- ToolValidator: Validates actions before execution

Example:
    ```python
    from agent.execution import AgentIterator, AgentActionExecutor, ExecutionMode
    
    iterator = AgentIterator(
        strategy=strategy,
        tool_executor=executor.execute,
        mode=ExecutionMode.AUTO
    )
    
    for step in iterator:
        if step.type == StepType.FINISH:
            break
    ```
"""

from .iterator import AgentIterator, ExecutionMode
from .executor import AgentActionExecutor, ToolValidator

__all__ = [
    "AgentIterator",
    "ExecutionMode", 
    "AgentActionExecutor",
    "ToolValidator"
]
