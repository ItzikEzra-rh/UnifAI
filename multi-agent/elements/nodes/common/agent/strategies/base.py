"""
Base agent strategy interface and utilities.

This module defines the core AgentStrategy protocol that all strategy
implementations must follow. Strategies are pure decision logic - they decide
what to do next but don't execute anything.

Design Principles:
- Single Responsibility: Strategy only decides what to do next
- No Execution: Strategies don't own or manage tool execution
- Pure Logic: Given messages and observations, return next steps
- Stateful: Strategies can maintain internal state between calls
"""

from abc import ABC, abstractmethod
from typing import List, Tuple, Dict, Any, Callable
from elements.llms.common.chat.message import ChatMessage, Role
from elements.tools.common.base_tool import BaseTool
from ..primitives import AgentAction, AgentObservation, AgentStep, StepType
from ..parsers import OutputParser, ParseError
from ..constants import StrategyDefaults


class AgentStrategy(ABC):
    """
    Abstract base class for agent planning strategies.
    
    Strategies are pure decision logic - they decide what to do next based on
    the current conversation state and observations. They don't execute actions
    or manage tools, just make decisions.
    
    Each strategy can implement different approaches:
    - ReAct: Interleaved reasoning and acting
    - PlanAndExecute: Plan multiple steps, then execute
    - Custom: Domain-specific approaches
    
    Strategies are stateful and can maintain internal counters, memory, etc.
    """
    
    def __init__(
        self, 
        *,
        llm_chat: Callable[[List[ChatMessage], List[BaseTool]], ChatMessage],
        tools: List[BaseTool],
        parser: OutputParser,
        max_steps: int = StrategyDefaults.MAX_STEPS
    ):
        """
        Initialize base strategy.
        
        Args:
            llm_chat: Function to call LLM with messages and tools
            tools: All available tools for this strategy
            parser: Output parser for converting LLM responses
            max_steps: Maximum planning steps before stopping
        """
        self.llm_chat = llm_chat
        self.all_tools = {tool.name: tool for tool in tools}
        self.parser = parser
        self.max_steps = max_steps
        self._step_count = 0
        self._error_count = 0
    
    @abstractmethod
    def get_tools_for_phase(self, phase: str, context: Dict[str, Any] = None) -> List[BaseTool]:
        """
        Get tools to expose to LLM for current phase.
        
        This allows strategies to control which tools are available at different
        stages of execution. For example, PlanAndExecute might only expose 
        planning tools during planning phase.
        
        Args:
            phase: Current execution phase (strategy-specific)
            context: Optional context for phase-specific decisions
            
        Returns:
            List of tools to expose to LLM for this phase
        """
        ...
    
    @abstractmethod
    def think(
        self, 
        messages: List[ChatMessage],
        observations: List[AgentObservation]
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
        observations: List[AgentObservation]
    ) -> str:
        """
        Format observation history for LLM context.
        
        Converts observations into a text format that can be included in the
        LLM prompt. Can be overridden by strategies that need custom formatting.
        
        Args:
            observations: Observations to format
            
        Returns:
            Formatted text representation of observations
        """
        if not observations:
            return ""
        
        formatted = []
        for i, obs in enumerate(observations, 1):
            entry = [f"Step {i}:"]
            entry.append(f"Tool: {obs.tool}")
            
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
        observations: List[AgentObservation],
        additional_context: str = ""
    ) -> List[ChatMessage]:
        """
        Build complete context for LLM including observations.
        
        Combines the original messages with formatted observations and
        any additional context. Can be overridden for custom context building.
        
        Args:
            messages: Original conversation messages
            observations: Observation history
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
        determines how to respond. Default implementation creates an error step.
        
        Args:
            error: The parsing error that occurred
            
        Returns:
            List of steps to handle the error
        """
        self._error_count += 1
        
        # Create terminal error step
        return [AgentStep(StepType.ERROR, error, metadata={
            "error_type": "parse_error", 
            "error_count": self._error_count,
            "recoverable": getattr(error, 'recoverable', False)
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
