"""
Agent capability mixin for nodes.

This module provides the AgentCapableMixin that orchestrates the agent system
components into a cohesive capability that can be added to nodes. It integrates
with existing mixins (LLM, Tool, BaseNode) to provide agent behavior.

Design Principles:
- Composition over Inheritance: Uses existing capabilities
- Configuration-driven: Behavior controlled via config objects  
- Multiple APIs: Simple (run_agent) and advanced (create_iterator)
- SOLID compliance: Depends on interfaces, not implementations
"""

import time
from dataclasses import dataclass
from typing import Optional, List, Dict, Any, TypeVar, Generic, Iterator, Callable
from enum import Enum

from elements.llms.common.chat.message import ChatMessage, Role
from agent import (
    AgentAction, AgentObservation, AgentFinish, AgentStep, StepType,
    AgentConfig
)
from agent.parsers import OutputParser, ToolCallParser, ParseError
from agent.strategies import AgentStrategy, ReActStrategy
from agent.execution import AgentIterator, ExecutionMode, ToolExecutor, ToolValidator
from agent.constants import (
    StrategyType, EarlyStoppingPolicy, ExecutionDefaults,
    ToolHandlingPolicy, ToolExecutionDefaults, StrategyDefaults
)
from core.contracts import SupportsStreaming

T = TypeVar("T", bound=SupportsStreaming)


class AgentCapableMixin(Generic[T]):
    """
    Mixin that adds agent capabilities to nodes.
    
    Orchestrates the agent system components to provide high-level agent
    behavior. Integrates with existing node capabilities (LLM, tools, streaming)
    to create a complete agent execution system.
    
    Required Mixins (checked via __init_subclass__):
    - LlmCapableMixin: Provides _chat() method
    - ToolCapableMixin: Provides tools and invoke_tools()  
    - BaseNode: Provides _stream() and is_streaming()
    
    Public APIs:
    - run_agent(): Simple automatic execution
    - stream_agent(): Real-time streaming execution
    - create_iterator(): Advanced step-by-step control
    
    Example:
        class MyAgentNode(
            AgentCapableMixin,
            ToolCapableMixin, 
            LlmCapableMixin,
            BaseNode
        ):
            def run(self, state):
                messages = self._build_messages(state)
                result = self.run_agent(messages)
                return result
    """
    
    def __init_subclass__(cls) -> None:
        """
        Verify that required capabilities are present.
        
        Checks that the class has the required methods from other mixins
        to ensure proper composition.
        """
        required_attrs = ["_chat", "tools", "invoke_tools", "_stream", "is_streaming"]
        missing = []
        
        for attr in required_attrs:
            if not any(hasattr(base, attr) for base in cls.__mro__):
                missing.append(attr)
        
        if missing:
            capabilities_map = {
                "_chat": "LlmCapableMixin",
                "tools": "ToolCapableMixin", 
                "invoke_tools": "ToolCapableMixin",
                "_stream": "BaseNode",
                "is_streaming": "BaseNode"
            }
            missing_mixins = {capabilities_map[attr] for attr in missing}
            raise TypeError(
                f"{cls.__name__} requires {', '.join(missing_mixins)} "
                f"to provide: {missing}"
            )
        
        super().__init_subclass__()
    
    def create_agent_strategy(
        self,
        strategy_type: str = StrategyType.REACT.value,
        *,
        parser: Optional[OutputParser] = None,
        **kwargs
    ) -> AgentStrategy:
        """
        Factory method for creating agent strategies.
        
        Supports different strategy types and custom configuration.
        New strategies can be added by extending this method.
        
        Args:
            strategy_type: Type of strategy ("react", "plan_execute", etc.)
            parser: Custom output parser (default: ToolCallParser)
            **kwargs: Strategy-specific configuration
            
        Returns:
            Configured AgentStrategy instance
            
        Raises:
            ValueError: If strategy_type is unknown
        """
        if parser is None:
            parser = ToolCallParser()
        
        if strategy_type == StrategyType.REACT.value:
            return ReActStrategy(
                llm_chat=self._chat,  # From LlmCapableMixin
                parser=parser,
                **kwargs
            )
        elif strategy_type == StrategyType.PLAN_AND_EXECUTE.value:
            # Future implementation
            from agent.strategies.plan_execute import PlanExecuteStrategy
            return PlanExecuteStrategy(
                llm_chat=self._chat,
                parser=parser,
                **kwargs
            )
        # Add more strategies here
        
        raise ValueError(f"Unknown strategy type: {strategy_type}")
    
    def create_tool_executor(self, config: AgentConfig) -> ToolExecutor:
        """
        Create tool executor using existing tool capabilities.
        
        Bridges agent actions to the existing ToolCapableMixin system.
        
        Args:
            config: Agent configuration
            
        Returns:
            Configured ToolExecutor
        """
        return ToolExecutor(
            tools=self.tools,  # From ToolCapableMixin
            tool_invoke_fn=self.invoke_tools,  # From ToolCapableMixin
            validate_args=config.validate_tools,
            on_missing_tool=config.on_missing_tool
        )
    
    def create_tool_validator(self, config: AgentConfig) -> Optional[ToolValidator]:
        """
        Create tool validator based on configuration.
        
        Args:
            config: Agent configuration
            
        Returns:
            ToolValidator if validation is enabled, None otherwise
        """
        if not config.validate_tools and not config.allowed_tools and not config.forbidden_tools:
            return None
        
        return ToolValidator(
            tools={tool.name: tool for tool in self.tools},
            allowed_tools=config.allowed_tools,
            forbidden_tools=config.forbidden_tools,
            max_actions_per_minute=config.max_actions_per_minute
        )
    
    def create_agent_iterator(
        self,
        messages: List[ChatMessage],
        *,
        config: Optional[AgentConfig] = None,
        strategy: Optional[AgentStrategy] = None,
        on_action: Optional[Callable[[AgentAction], bool]] = None
    ) -> AgentIterator:
        """
        Create iterator for step-by-step agent execution.
        
        Provides fine-grained control over agent execution with support
        for different modes and custom callbacks.
        
        Args:
            messages: Initial conversation messages
            config: Agent configuration (uses defaults if None)
            strategy: Custom strategy (creates from config if None)
            on_action: Callback to approve/reject actions
            
        Returns:
            Configured AgentIterator for step-by-step execution
        """
        if config is None:
            config = AgentConfig()
        
        # Create or use provided strategy
        if strategy is None:
            if config.custom_strategy:
                strategy = config.custom_strategy
            else:
                strategy = self.create_agent_strategy(
                    strategy_type=config.strategy,
                    parser=config.custom_parser,
                    max_steps=config.max_steps,
                    reflect_on_errors=config.reflect_on_errors
                )
        
        # Create tool executor and validator
        tool_executor = self.create_tool_executor(config)
        tool_validator = self.create_tool_validator(config)
        
        # Create iterator
        iterator = AgentIterator(
            strategy=strategy,
            tool_executor=tool_executor.execute,
            tool_validator=tool_validator,
            stream=self._stream if self.is_streaming() else None,
            mode=config.execution_mode,
            on_action=on_action
        )
        
        # Set initial messages
        iterator.messages = list(messages)
        
        return iterator
    
    def run_agent(
        self,
        messages: List[ChatMessage],
        *,
        config: Optional[AgentConfig] = None
    ) -> Dict[str, Any]:
        """
        High-level API: Run agent to completion automatically.
        
        Simple interface for automatic agent execution. Creates an iterator
        and runs it to completion, returning the final result.
        
        Args:
            messages: Initial conversation messages
            config: Agent configuration
            
        Returns:
            Dictionary with output, reasoning, and optional intermediate steps
        """
        if config is None:
            config = AgentConfig()
        
        iterator = self.create_agent_iterator(messages, config=config)
        
        result = {
            "output": None,
            "reasoning": "",
            "error": None,
            "success": False,
            "steps": [],
            "observations": [],
            "metadata": {}
        }
        
        start_time = time.time()
        
        try:
            for step in iterator:
                # Collect intermediate steps if requested
                if config.return_intermediate:
                    result["steps"].append(step)
                
                # Handle different step types
                if step.type == StepType.FINISH:
                    finish_data = step.data
                    result.update(finish_data.as_dict())
                    result["success"] = True
                    break
                    
                elif step.type == StepType.ERROR:
                    result["error"] = str(step.data)
                    result["success"] = False
                    if config.early_stopping == "first_error":
                        break
                
                # Check execution time limit
                if config.max_execution_time:
                    elapsed = time.time() - start_time
                    if elapsed > config.max_execution_time:
                        result["error"] = f"Execution timeout ({elapsed:.1f}s)"
                        result["success"] = False
                        break
            
            # If no output set and no error, agent completed without output
            if result["output"] is None and not result["error"]:
                result["output"] = "Agent completed without producing output"
                result["success"] = False
                
        except Exception as e:
            result["error"] = f"Unexpected error: {e}"
            result["success"] = False
        
        # Add execution metadata
        result["metadata"] = {
            "execution_time": time.time() - start_time,
            "total_steps": len(iterator.history),
            "observations": len(iterator.observations),
            "strategy": config.strategy,
            "execution_mode": config.execution_mode.value
        }
        
        # Include intermediate data if requested
        if config.return_intermediate:
            result["observations"] = iterator.observations
            result["history"] = iterator.history
        
        return result
    
    def stream_agent(
        self,
        messages: List[ChatMessage],
        *,
        config: Optional[AgentConfig] = None,
        on_action: Optional[Callable[[AgentAction], bool]] = None
    ) -> Iterator[Dict[str, Any]]:
        """
        Stream agent execution events in real-time.
        
        Yields execution events as they occur, allowing for real-time
        monitoring and intervention. Useful for UI integration.
        
        Args:
            messages: Initial conversation messages
            config: Agent configuration
            on_action: Callback to approve/reject actions
            
        Yields:
            Dictionary events with type, data, and metadata
        """
        if config is None:
            config = AgentConfig()
        
        # For streaming, we want manual control over execution
        stream_config = AgentConfig(
            **config.__dict__,
            execution_mode=ExecutionMode.MANUAL
        )
        
        iterator = self.create_agent_iterator(
            messages, 
            config=stream_config,
            on_action=on_action
        )
        
        pending_actions = []
        start_time = time.time()
        
        try:
            for step in iterator:
                # Yield step event
                yield {
                    "type": f"agent_{step.type.value}",
                    "data": self._serialize_step(step),
                    "timestamp": step.timestamp,
                    "metadata": step.metadata
                }
                
                # Handle actions in manual mode
                if step.type == StepType.ACTION:
                    action = step.data
                    pending_actions.append(action)
                    
                    # Auto-execute (since we're streaming)
                    tool_executor = self.create_tool_executor(config)
                    obs = tool_executor.execute(action)
                    iterator.feed_observation(action, obs)
                    
                    # Yield observation event
                    yield {
                        "type": "agent_observation",
                        "data": {
                            "action_id": action.id,
                            "tool": action.tool,
                            "output": obs.content,
                            "success": obs.success,
                            "execution_time": obs.execution_time,
                            "error": str(obs.error) if obs.error else None
                        },
                        "timestamp": time.time(),
                        "metadata": {"action_id": action.id}
                    }
                
                elif step.type == StepType.FINISH:
                    # Yield final summary
                    yield {
                        "type": "agent_complete",
                        "data": {
                            "output": step.data.output,
                            "reasoning": step.data.reasoning,
                            "success": True,
                            "execution_time": time.time() - start_time,
                            "total_steps": len(iterator.history),
                            "actions_taken": len(pending_actions)
                        },
                        "timestamp": time.time(),
                        "metadata": {"final": True}
                    }
                    break
                
                elif step.type == StepType.ERROR:
                    yield {
                        "type": "agent_error", 
                        "data": {
                            "error": str(step.data),
                            "recoverable": getattr(step.data, 'recoverable', False),
                            "execution_time": time.time() - start_time
                        },
                        "timestamp": time.time(),
                        "metadata": {"error": True}
                    }
                    
                    if config.early_stopping == "first_error":
                        break
                        
        except Exception as e:
            yield {
                "type": "agent_error",
                "data": {
                    "error": f"Unexpected error: {e}",
                    "execution_time": time.time() - start_time
                },
                "timestamp": time.time(),
                "metadata": {"unexpected_error": True}
            }
    
    def _serialize_step(self, step: AgentStep) -> Dict[str, Any]:
        """
        Serialize step data for streaming/API consumption.
        
        Args:
            step: AgentStep to serialize
            
        Returns:
            Dictionary representation of step data
        """
        if step.type == StepType.ACTION:
            action = step.data
            return {
                "id": action.id,
                "tool": action.tool,
                "tool_input": action.tool_input,
                "reasoning": action.reasoning,
                "status": action.status.value
            }
            
        elif step.type == StepType.OBSERVATION:
            obs = step.data
            return {
                "action_id": obs.action_id,
                "tool": obs.tool,
                "output": obs.output,
                "success": obs.success,
                "execution_time": obs.execution_time,
                "error": str(obs.error) if obs.error else None
            }
            
        elif step.type == StepType.FINISH:
            finish = step.data
            return finish.as_dict()
            
        elif step.type == StepType.ERROR:
            return {
                "error": str(step.data),
                "error_type": type(step.data).__name__,
                "recoverable": getattr(step.data, 'recoverable', False)
            }
            
        elif step.type == StepType.PLANNING:
            if hasattr(step.data, 'content'):
                return {"reasoning": step.data.content}
            return {"data": str(step.data)}
        
        # Fallback
        return {"data": str(step.data)}
