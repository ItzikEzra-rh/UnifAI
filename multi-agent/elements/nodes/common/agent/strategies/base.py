"""
Base agent strategy interface and utilities.

This module defines the core AgentStrategy protocol that all strategy
implementations must follow. Provides common utilities for context building,
observation formatting, and step management.

Design Principles:
- Single Responsibility: Strategy only decides what to do next
- Open/Closed: Easy to add new strategies without modifying existing code
- Protocol-based: Clear interface with type checking support
- Stateful: Strategies can maintain internal state between calls
"""

from abc import ABC, abstractmethod
from typing import List, Tuple, Protocol, runtime_checkable, Callable
from elements.llms.common.chat.message import ChatMessage, Role
from ..primitives import AgentAction, AgentObservation, AgentStep, StepType, ExecutionHistory
from ..parsing import OutputParser, ParseError
from ..constants import StrategyDefaults


@runtime_checkable
class SupportsToolValidation(Protocol):
    """
    Protocol for components that can validate agent actions.
    
    Used by strategies to check if actions are valid before
    yielding them for execution.
    """
    
    def validate_action(self, action: AgentAction) -> Tuple[bool, str]:
        """
        Validate if an action can be executed.
        
        Args:
            action: Action to validate
            
        Returns:
            (is_valid, error_message) tuple
        """
        ...


class AgentStrategy(ABC):
    """
    Abstract base class for agent planning strategies.
    
    Strategies implement the "thinking" part of the agent - deciding what
    actions to take based on the current conversation state and observation
    history. Each strategy can implement different approaches:
    
    - ReAct: Interleaved reasoning and acting
    - PlanAndExecute: Plan multiple steps, then execute
    - TreeOfThoughts: Explore multiple reasoning paths
    - Custom: Domain-specific approaches
    
    Strategies are stateful and can maintain internal counters, memory, etc.
    """
    
    def __init__(
        self, 
        *, 
        parser: OutputParser,
        max_steps: int = StrategyDefaults.MAX_STEPS,
        reflect_on_errors: bool = StrategyDefaults.REFLECT_ON_ERRORS
    ):
        """
        Initialize base strategy.
        
        Args:
            parser: Output parser for converting LLM responses
            max_steps: Maximum planning steps before stopping
            reflect_on_errors: Whether to create reflection actions for errors
        """
        self.parser = parser
        self.max_steps = max_steps
        self.reflect_on_errors = reflect_on_errors
        self._step_count = 0
        self._error_count = 0
    
    @abstractmethod
    def think(
        self, 
        messages: List[ChatMessage],
        observations: List[Tuple[AgentAction, AgentObservation]]
    ) -> List[AgentStep]:
        """
        Generate next steps based on current state.
        
        This is the core method that implements the strategy's decision-making
        logic. Based on the conversation history and previous observations,
        determine what the agent should do next.
        
        Args:
            messages: Conversation history (user messages, system prompts, etc.)
            observations: History of actions taken and their results
            
        Returns:
            List of steps to execute (planning, actions, finish, etc.)
            
        Raises:
            ParseError: If LLM output cannot be parsed
            RuntimeError: If strategy encounters unrecoverable error
        """
        ...
    
    @abstractmethod  
    def should_continue(self, history: List[AgentStep]) -> bool:
        """
        Check if strategy should continue execution.
        
        Examines the execution history to determine if the agent should
        keep going or stop. Considers factors like:
        - Maximum step limits
        - Terminal states (finish/error)
        - Strategy-specific stopping conditions
        
        Args:
            history: Complete execution history
            
        Returns:
            True if execution should continue, False otherwise
        """
        ...
    
    def format_observations(
        self, 
        observations: List[Tuple[AgentAction, AgentObservation]]
    ) -> str:
        """
        Format observation history for LLM context.
        
        Converts the action-observation pairs into a text format that
        can be included in the LLM prompt. Can be overridden by strategies
        that need custom formatting.
        
        Args:
            observations: Action-observation pairs to format
            
        Returns:
            Formatted text representation of observations
        """
        if not observations:
            return ""
        
        formatted = []
        for i, (action, obs) in enumerate(observations, 1):
            entry = [f"Step {i}:"]
            entry.append(f"Action: {action.tool}")
            entry.append(f"Input: {action.tool_input}")
            
            if obs.success:
                entry.append(f"Result: {obs.output}")
            else:
                entry.append(f"Error: {obs.error}")
                entry.append(f"Execution time: {obs.execution_time:.3f}s")
            
            formatted.append("\n".join(entry))
        
        return "\n\n".join(formatted)
    
    def build_context(
        self,
        messages: List[ChatMessage],
        observations: List[Tuple[AgentAction, AgentObservation]],
        additional_context: str = ""
    ) -> List[ChatMessage]:
        """
        Build complete context for LLM including observations.
        
        Combines the original messages with formatted observations and
        any additional context. Can be overridden for custom context building.
        
        Args:
            messages: Original conversation messages
            observations: Action-observation history
            additional_context: Extra context to include
            
        Returns:
            Complete message list for LLM
        """
        context = list(messages)
        
        # Add observation history if present
        if observations:
            obs_text = self.format_observations(observations)
            context.append(ChatMessage(
                role=Role.SYSTEM,
                content=f"Previous actions and observations:\n{obs_text}"
            ))
        
        # Add any additional context
        if additional_context:
            context.append(ChatMessage(
                role=Role.SYSTEM, 
                content=additional_context
            ))
        
        return context
    
    def handle_parse_error(self, error: ParseError) -> List[AgentStep]:
        """
        Handle LLM output parsing errors.
        
        When the LLM output cannot be parsed into valid actions, this method
        determines how to respond. Can create reflection actions or stop execution.
        
        Args:
            error: The parsing error that occurred
            
        Returns:
            List of steps to handle the error (usually reflection actions)
        """
        self._error_count += 1
        
        if self.reflect_on_errors and error.recoverable:
            # Create reflection action
            reflection_action = self.parser.parse_error_recovery(error)
            return [AgentStep(StepType.ACTION, reflection_action, metadata={
                "error_type": "parse_error",
                "error_count": self._error_count,
                "recoverable": error.recoverable
            })]
        else:
            # Create terminal error step
            return [AgentStep(StepType.ERROR, error, metadata={
                "error_type": "parse_error", 
                "error_count": self._error_count,
                "recoverable": error.recoverable
            })]
    
    def increment_step_count(self) -> None:
        """Increment internal step counter."""
        self._step_count += 1
    
    def reset_counters(self) -> None:
        """Reset internal counters (useful for reusing strategy instances)."""
        self._step_count = 0 
        self._error_count = 0
    
    @property
    def step_count(self) -> int:
        """Current step count."""
        return self._step_count
    
    @property
    def error_count(self) -> int:
        """Current error count."""
        return self._error_count
