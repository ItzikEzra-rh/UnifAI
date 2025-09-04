"""
Agent system configuration classes and utilities.

This module provides configuration dataclasses for controlling all aspects
of agent behavior including strategy selection, execution modes, error handling,
and performance limits.

Design Principles:
- Centralized Configuration: All agent config in one place
- Type Safety: Use enums and proper types for validation
- Reasonable Defaults: Sensible defaults for quick setup
- Extensibility: Easy to add new configuration options
"""

from dataclasses import dataclass
from typing import Optional, List

from .constants import (
    StrategyType, StrategyDefaults, ExecutionDefaults,
    ToolExecutionDefaults, ToolHandlingPolicy, EarlyStoppingPolicy
)
from .execution import ExecutionMode
from .parsers import OutputParser
from .strategies import AgentStrategy


@dataclass
class AgentConfig:
    """
    Configuration for agent execution.
    
    Controls all aspects of agent behavior including strategy selection,
    execution mode, error handling, and performance limits.
    
    Example:
        config = AgentConfig(
            strategy=StrategyType.REACT.value,
            execution_mode=ExecutionMode.GUIDED,
            max_steps=15,
            max_execution_time=300.0
        )
        
        result = agent.run_agent(messages, config=config)
    """
    # Strategy configuration
    strategy: str = StrategyType.REACT.value
    max_steps: int = StrategyDefaults.MAX_STEPS
    reflect_on_errors: bool = StrategyDefaults.REFLECT_ON_ERRORS
    
    # Execution configuration  
    execution_mode: ExecutionMode = ExecutionMode.AUTO
    validate_tools: bool = ToolExecutionDefaults.VALIDATE_ARGS
    allowed_tools: Optional[List[str]] = None
    forbidden_tools: Optional[List[str]] = None
    
    # Error handling
    on_missing_tool: str = ToolHandlingPolicy.REFLECT.value
    early_stopping: str = EarlyStoppingPolicy.FIRST_FINISH.value
    return_intermediate: bool = ExecutionDefaults.RETURN_INTERMEDIATE
    
    # Performance limits
    max_execution_time: Optional[float] = ExecutionDefaults.MAX_EXECUTION_TIME
    max_actions_per_minute: Optional[int] = ExecutionDefaults.MAX_ACTIONS_PER_MINUTE
    
    # Custom components
    custom_parser: Optional[OutputParser] = None
    custom_strategy: Optional[AgentStrategy] = None


# Future extension examples for when we add more config classes:

# @dataclass
# class StrategyConfig:
#     """Configuration for specific strategies."""
#     pass

# @dataclass  
# class ExecutionConfig:
#     """Configuration for execution behavior."""
#     pass

# @dataclass
# class ParserConfig:
#     """Configuration for output parsing."""
#     pass

# class AgentConfigBuilder:
#     """Builder pattern for complex configurations."""
#     pass

# class ConfigTemplates:
#     """Pre-built configuration templates for common use cases."""
#     
#     @staticmethod
#     def development() -> AgentConfig:
#         """Development-friendly config with verbose output."""
#         return AgentConfig(
#             execution_mode=ExecutionMode.GUIDED,
#             return_intermediate=True,
#             reflect_on_errors=True
#         )
#     
#     @staticmethod
#     def production() -> AgentConfig:
#         """Production config optimized for performance."""
#         return AgentConfig(
#             execution_mode=ExecutionMode.AUTO,
#             return_intermediate=False,
#             max_execution_time=60.0
#         )
#     
#     @staticmethod
#     def safe() -> AgentConfig:
#         """Safety-first config with human oversight."""
#         return AgentConfig(
#             execution_mode=ExecutionMode.GUIDED,
#             validate_tools=True,
#             max_steps=5,
#             early_stopping=EarlyStoppingPolicy.FIRST_ERROR.value
#         )