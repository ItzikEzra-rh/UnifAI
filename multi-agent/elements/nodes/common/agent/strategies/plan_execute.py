"""
Plan and Execute agent strategy.

This strategy implements a phased approach where the agent:
1. Plans work by creating/updating a WorkPlan
2. Allocates work items to local/remote execution
3. Executes local work items
4. Monitors progress and responses
5. Synthesizes results

Each phase exposes different tools to enforce clean separation of concerns.
"""

from typing import List, Dict, Any, Optional, Callable
from enum import Enum
from elements.llms.common.chat.message import ChatMessage, Role
from elements.tools.common.base_tool import BaseTool
from ..primitives import AgentStep, StepType, AgentFinish, AgentObservation
from ..parsers import OutputParser
from .base import AgentStrategy
from ..constants import (
    StrategyDefaults, StrategyType, SystemPrompts, ExecutionPhase
)
from ..phases.phase_protocols import PhaseState, WorkPlanStatus
from ..phases.unified_phase_provider import PhaseProvider  # Uses PhaseProvider abstraction




class PlanAndExecuteStrategy(AgentStrategy):
    """
    Plan and Execute strategy - SOLID compliant.
    
    Delegates ALL phase logic to PhaseProvider:
    - No hardcoded phase names
    - No knowledge of provider internals (cascade, iteration, limits)
    - No interpretation of provider implementation details
    
    Strategy responsibilities:
    - Execution flow (think → act → observe loop)
    - Tool execution coordination
    - LLM interaction
    - Step creation
    
    Provider responsibilities:
    - Phase definitions and transitions
    - Cascade logic (if any)
    - Iteration tracking (if any)
    - All phase-specific logic
    """
    
    def __init__(
        self,
        *,
        llm_chat: Callable[[List[ChatMessage], List[BaseTool]], ChatMessage],
        tools: List[BaseTool],
        parser: OutputParser,
        max_steps: int = StrategyDefaults.MAX_STEPS,
        system_message: Optional[str] = None,
        max_planning_iterations: int = 3,
        max_allocation_iterations: int = 3,
        phase_provider: Optional[PhaseProvider] = None
    ):
        """
        Initialize Plan and Execute strategy.
        
        Args:
            llm_chat: Function to call LLM with messages and tools
            tools: All available tools for this strategy (fallback)
            parser: Output parser for LLM responses
            max_steps: Maximum total steps before stopping
            system_message: System message from node (takes priority)
            max_planning_iterations: Max iterations in planning phase
            max_allocation_iterations: Max iterations in allocation phase
            phase_provider: Unified provider for all phase-related concerns
        """
        super().__init__(
            llm_chat=llm_chat,
            tools=tools,
            parser=parser,
            max_steps=max_steps,
            system_message=system_message
        )
        
        self.max_planning_iterations = max_planning_iterations
        self.max_allocation_iterations = max_allocation_iterations
        self._phase_iterations = 0
        self._no_progress_count = 0
        
        # Store phase provider (required)
        if not phase_provider:
            raise ValueError("PlanAndExecuteStrategy requires a phase_provider")
        self._phase_provider = phase_provider
        
        # Get initial phase from provider (NOT hardcoded)
        self._current_phase = self._phase_provider.get_initial_phase()
    
    @property
    def strategy_name(self) -> str:
        """Return the name of this strategy."""
        return StrategyType.PLAN_AND_EXECUTE.value
    
    def get_tools_for_phase(self, phase: str, context: Dict[str, Any] = None) -> List[BaseTool]:
        """
        Get tools to expose for current phase.
        
        The strategy is agnostic to tool types - it delegates to the
        phase tool provider injected by the node.
        
        Args:
            phase: Current execution phase (string for base class compatibility)
            context: Optional context (unused, for future extensibility)
            
        Returns:
            List of tools appropriate for this phase
        """
        # Use phase provider to get tools (phase provider handles string/enum conversion)
        try:
            tools = self._phase_provider.get_tools_for_phase(phase)
            return tools
        except Exception as e:
            # Fallback to all tools
            pass
        
        # Fallback to all tools if no provider or invalid phase
        all_tools = list(self.all_tools.values())
        return all_tools
    
    def think(
        self,
        messages: List[ChatMessage],
        observations: List[AgentObservation]
    ) -> List[AgentStep]:
        """
        Generate next steps based on current phase and state.
        
        Implements phase transitions and appropriate tool exposure.
        Each phase may iterate multiple times before transitioning.
        
        Args:
            messages: Conversation history
            observations: Previous tool execution results
            
        Returns:
            List of steps to execute
        """
        # Visual banner at start of FIRST think call (before phase updates)
        if self._step_count == 0:
            print(f"\n{'='*80}")
            print(f"🧠 LLM INTERACTION #1 - BEGINNING ORCHESTRATION CYCLE")
            print(f"📍 Starting Phase: {self._current_phase.upper()}")
            print(f"{'='*80}\n")
        else:
            print(f"📍 Phase: {self._current_phase}")
        
        try:
            # Determine current phase based on context
            # _update_phase now handles cascading transitions internally
            old_phase = self._current_phase
            self._update_phase(observations)
            if old_phase != self._current_phase:
                print(f"   └─ Phase Transition: {old_phase} → {self._current_phase}")
            
            # Build phase-specific context
            context = self.build_context(messages, observations)
            
            # Get phase-appropriate tools
            tools = self.get_tools_for_phase(self._current_phase)
            
            # If no tools available and phase requires tools, advance
            if not tools and self._phase_provider.requires_tools(self._current_phase):
                self._advance_phase()
                return self.think(messages, observations)
            
            # Get LLM response
            response = self.llm_chat(context, tools)
            
            # Parse response
            result = self.parser.parse(response)
            
            # Create steps
            steps = [AgentStep(StepType.PLANNING, response, metadata={
                "phase": self._current_phase,
                "iteration": self._phase_iterations
            })]
            
            # Handle parsed result
            if isinstance(result, list):
                # Tool calls - create action steps
                for i, action in enumerate(result):
                    steps.append(AgentStep(
                        StepType.ACTION,
                        action,
                        metadata={"phase": self._current_phase}
                    ))
            elif isinstance(result, AgentFinish):
                # Agent wants to finish - ask PROVIDER if we can (SOLID!)
                can_finish = self._phase_provider.can_finish_now(self._current_phase)
                
                if not can_finish:
                    # Provider handles phase transition logic
                    self._update_phase(observations)
                    # Continue with new phase
                    return self.think(messages, observations)
                else:
                    # Provider allows finish
                    steps.append(AgentStep(StepType.FINISH, result))
            
            self.increment_step_count()
            self._phase_iterations += 1
            
            return steps
            
        except Exception as e:
            return [AgentStep(
                StepType.ERROR,
                e,
                metadata={"phase": self._current_phase}
            )]
    
    def build_context(
        self,
        messages: List[ChatMessage],
        observations: List[AgentObservation]
    ) -> List[ChatMessage]:
        """
        Build context with phase-specific prompting and dynamic context.
        
        Includes:
        - Phase-specific system message with guidance + validation
        - Static messages (conversation, adjacency, request)
        - Dynamic context from provider (fresh workspace + work plan)
        - Tool observations as TOOL messages
        
        Args:
            messages: Original conversation (static messages)
            observations: Tool execution results
            
        Returns:
            Complete context for LLM
        """
        context = []
        
        # [1] System message with phase guidance + validation
        system_content = self._build_phase_prompt()
        if self.system_message:
            system_content = f"{self.system_message}\n\n{system_content}"
        
        context.append(ChatMessage(role=Role.SYSTEM, content=system_content))
        
        # [2] Static messages (conversation, adjacency, request)
        # Filter out old workspace/workplan if provider has dynamic context
        static_messages = self._filter_static_messages(messages)
        context.extend(static_messages)
        
        # [3] Dynamic context from provider (fresh workspace + work plan)
        # This ensures LLM always sees current state
        if hasattr(self._phase_provider, 'get_dynamic_context_messages'):
            dynamic_context = self._phase_provider.get_dynamic_context_messages(
                self._current_phase
            )
            context.extend(dynamic_context)
        
        # [4] Tool observations
        for obs in observations:
            context.append(ChatMessage(
                role=Role.TOOL,
                content=str(obs.output) if obs.success else f"Error: {obs.error}",
                tool_call_id=obs.action_id
            ))
        
        return context
    
    def _filter_static_messages(self, messages: List[ChatMessage]) -> List[ChatMessage]:
        """
        Filter messages to only include truly static ones.
        
        If provider has dynamic context, skip workspace/workplan messages
        from original list (they'll be replaced with fresh ones).
        
        Args:
            messages: Original messages from orchestrator
            
        Returns:
            Filtered list of static messages
        """
        if not hasattr(self._phase_provider, 'get_dynamic_context_messages'):
            # No dynamic context support, return all messages
            return list(messages)
        
        # Skip messages that will be replaced by dynamic context
        static = []
        for msg in messages:
            content = msg.content or ""
            # Skip if it's workspace or work plan context (will be refreshed)
            if content.startswith("Current Context:") or content.startswith("Current Work Plan:"):
                continue
            static.append(msg)
        
        return static
    
    def should_continue(self, history: List[AgentStep]) -> bool:
        """
        Check if strategy should continue execution.
        
        Stops when:
        - Maximum steps reached
        - Terminal step encountered
        - No progress for multiple iterations
        - All phases complete
        
        Args:
            history: Execution history
            
        Returns:
            True if should continue
        """
        # Check for terminal steps
        if history and history[-1].is_terminal:
            return False
        
        # Check step limit
        if self._step_count >= self.max_steps:
            return False
        
        # Check for no progress
        if self._no_progress_count > 3:
            return False
        
        # Check if in terminal phase (ask provider, don't hardcode)
        # Terminal phases (like SYNTHESIS) need at least 2 iterations:
        # 1. Call synthesis tool (e.g., workplan.summarize)
        # 2. See results, return AgentFinish with summary
        if self._phase_provider.is_terminal_phase(self._current_phase):
            if self._phase_iterations > 1:  # ✅ Allow tool call + finish
                return False
        
        return True
    
    def _update_phase(self, observations: List[AgentObservation]) -> None:
        """
        Update phase using provider.
        
        Provider is completely opaque - strategy doesn't know:
        - If cascade happens
        - How many transitions occur
        - If iteration limits are checked
        - Any other internal logic
        
        Just: "I'm in phase X" → Provider → "Now in phase Y"
        
        Args:
            observations: Recent observations from tool execution
        """
        old_phase = self._current_phase
        
        # Provider returns new phase (all logic internal)
        self._current_phase = self._phase_provider.update_phase(
            current_phase=self._current_phase,
            observations=observations
        )
        
        self._phase_iterations = 0
    
    def _should_transition_phase(self, observations: List[AgentObservation]) -> bool:
        """
        Determine if we should transition to the next phase.
        
        Now uses work plan state instead of blind iteration counting.
        Phase transitions are handled by _update_phase() based on actual state.
        """
        # Phase transitions are now handled by _update_phase() 
        # based on work plan state, not iteration counting
        return False
    
    def _advance_phase(self) -> None:
        """
        Advance to next phase in sequence.
        
        Delegates to provider - NO hardcoded phase knowledge.
        """
        next_phase = self._phase_provider.get_next_phase_in_sequence(self._current_phase)
        if next_phase:
            self._current_phase = next_phase
            self._phase_iterations = 0
    
    
    def _build_phase_prompt(self) -> str:
        """
        Build phase-specific system prompt with validation guidance.
        
        Uses the new build_phase_prompt method from BasePhaseProvider
        to include both base guidance and validation feedback.
        """
        base_prompt = self.system_message or SystemPrompts.PLAN_AND_EXECUTE
        
        # Get enhanced phase guidance (includes validation)
        try:
            phase_guidance = self._phase_provider.build_phase_prompt(self._current_phase)
            if phase_guidance:
                return f"{base_prompt}\n\n{phase_guidance}"
        except Exception as e:
            # Fallback to basic guidance
            try:
                fallback_guidance = self._phase_provider.get_phase_guidance(self._current_phase)
                if fallback_guidance:
                    return f"{base_prompt}\n\n{fallback_guidance}"
            except Exception as e2:
                pass
        
        return base_prompt
