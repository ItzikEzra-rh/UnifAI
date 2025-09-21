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
from ..phase_protocols import PhaseState, WorkPlanStatus
from ..unified_phase_provider import PhaseProvider




class PlanAndExecuteStrategy(AgentStrategy):
    """
    Plan and Execute strategy implementation.
    
    Creates and executes work plans with clear phase separation:
    - Planning: Create/update work plan
    - Allocation: Assign work to local/remote targets
    - Execution: Run local work items
    - Monitoring: Track progress and handle responses
    - Synthesis: Summarize results
    
    Features:
    - Phase-based tool exposure
    - Support for local and remote execution
    - Graceful degradation when tools missing
    - Re-entrant for graph-based execution
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
        
        # Store phase provider (required - no default)
        if not phase_provider:
            raise ValueError("PlanAndExecuteStrategy requires a phase_provider")
        self._phase_provider = phase_provider
        
        # Get initial phase from provider (not hardcoded)
        supported_phases = self._phase_provider.get_supported_phases()
        self._current_phase = supported_phases[0] if supported_phases else "planning"
    
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
        print(f"🔧 [DEBUG] get_tools_for_phase() - Requested phase: {phase}")
        
        # Use phase provider to get tools (phase provider handles string/enum conversion)
        try:
            tools = self._phase_provider.get_tools_for_phase(phase)
            print(f"🔧 [DEBUG] Provider returned {len(tools)} tools for {phase}: {[t.name for t in tools]}")
            return tools
        except Exception as e:
            print(f"Error getting phase tools: {e}")
            # Fallback to all tools
        
        # Fallback to all tools if no provider or invalid phase
        all_tools = list(self.all_tools.values())
        print(f"🔧 [DEBUG] Using fallback - returning all {len(all_tools)} tools")
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
        print(f"\n🧠 [DEBUG] PlanAndExecuteStrategy.think() - Starting")
        print(f"📊 [DEBUG] Current phase: {self._current_phase}")
        print(f"📝 [DEBUG] Messages: {len(messages)}, Observations: {len(observations)}")
        
        try:
            # Determine current phase based on context
            print(f"🔄 [DEBUG] Updating phase based on observations")
            old_phase = self._current_phase
            self._update_phase(observations)
            if old_phase != self._current_phase:
                print(f"🔄 [DEBUG] Phase transition: {old_phase} → {self._current_phase}")
            else:
                print(f"🔄 [DEBUG] Staying in phase: {self._current_phase}")
            
            # No automatic actions - strategy only manages phases
            # All actions should be done by LLM using appropriate tools
            
            # Build phase-specific context
            print(f"💬 [DEBUG] Building context for phase {self._current_phase}")
            context = self.build_context(messages, observations)
            print(f"💬 [DEBUG] Built context with {len(context)} messages")
            
            # Get phase-appropriate tools
            print(f"🔧 [DEBUG] Getting tools for phase {self._current_phase}")
            tools = self.get_tools_for_phase(self._current_phase)
            
            # If no tools available for this phase, skip it
            if not tools and self._current_phase != "synthesis":
                print(f"⚠️ [DEBUG] No tools for phase {self._current_phase}, advancing")
                self._advance_phase()
                return self.think(messages, observations)
            
            # Get LLM response
            print(f"🤖 [DEBUG] Calling LLM with {len(tools)} tools")
            response = self.llm_chat(context, tools)
            print(f"🤖 [DEBUG] LLM response received: {str(response)[:100]}...")
            
            # Parse response
            print(f"📝 [DEBUG] Parsing LLM response")
            result = self.parser.parse(response)
            print(f"📝 [DEBUG] Parsed result type: {type(result)}")
            
            # Create steps
            steps = [AgentStep(StepType.PLANNING, response, metadata={
                "phase": self._current_phase,
                "iteration": self._phase_iterations
            })]
            print(f"📋 [DEBUG] Created planning step for phase {self._current_phase}")
            
            # Handle parsed result
            if isinstance(result, list):
                # Tool calls - create action steps
                print(f"🔧 [DEBUG] Processing {len(result)} tool calls")
                for i, action in enumerate(result):
                    print(f"🔧 [DEBUG] Tool call {i+1}: {getattr(action, 'tool', 'unknown')}")
                    steps.append(AgentStep(
                        StepType.ACTION,
                        action,
                        metadata={"phase": self._current_phase}
                    ))
            elif isinstance(result, AgentFinish):
                # Finish - but check if we should transition phases instead
                print(f"🏁 [DEBUG] Agent wants to finish, checking if should transition")
                if self._should_transition_phase(observations):
                    print(f"🔄 [DEBUG] Transitioning phase instead of finishing")
                    self._advance_phase()
                    # Continue with next phase
                    return self.think(messages, observations)
                else:
                    # True finish
                    print(f"🏁 [DEBUG] True finish - adding finish step")
                    steps.append(AgentStep(StepType.FINISH, result))
            
            self.increment_step_count()
            self._phase_iterations += 1
            
            print(f"📋 [DEBUG] Returning {len(steps)} steps for phase {self._current_phase}")
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
        Build context with phase-specific prompting.
        
        Includes:
        - Phase-specific system message
        - Original messages
        - Tool observations as TOOL messages
        - Phase transition hints
        
        Args:
            messages: Original conversation
            observations: Tool execution results
            
        Returns:
            Complete context for LLM
        """
        context = []
        
        # System message with phase guidance
        system_content = self._build_phase_prompt()
        if self.system_message:
            system_content = f"{self.system_message}\n\n{system_content}"
        
        context.append(ChatMessage(role=Role.SYSTEM, content=system_content))
        
        # Original messages
        context.extend(messages)
        
        # Tool observations
        for obs in observations:
            context.append(ChatMessage(
                role=Role.TOOL,
                content=str(obs.output) if obs.success else f"Error: {obs.error}",
                tool_call_id=obs.action_id
            ))
        
        return context
    
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
        
        # Check if all phases complete
        if self._current_phase == ExecutionPhase.SYNTHESIS and self._phase_iterations > 0:
            return False
        
        return True
    
    def _update_phase(self, observations: List[AgentObservation]) -> None:
        """
        Update current phase based on observations and work plan state.
        
        Uses injected PhaseTransitionPolicy if available, otherwise falls back
        to built-in heuristics. This allows nodes to customize phase logic.
        """
        print(f"🔄 [DEBUG] _update_phase() - Current: {self._current_phase}")
        
        # Use phase provider for transitions
        print(f"🔀 [DEBUG] Using phase provider for transition")
        try:
            context = self._phase_provider.get_phase_context()
            print(f"📊 [DEBUG] Phase context: total_items={context.work_plan_status.total_items if context.work_plan_status else 'None'}")
            new_phase = self._phase_provider.decide_next_phase(
                current_phase=self._current_phase,
                context=context,
                observations=observations
            )
            print(f"🔀 [DEBUG] Provider decided: {self._current_phase} → {new_phase}")
            self._current_phase = new_phase
            return
        except Exception as e:
            print(f"❌ [DEBUG] Error using phase provider: {e}")
            # Fall through to built-in logic
        
        # Built-in fallback logic
        print(f"🔄 [DEBUG] Using built-in phase logic")
        plan_status = self._get_work_plan_status()
        
        if not plan_status:
            # No plan exists - should be in planning
            print(f"📋 [DEBUG] No plan status - going to PLANNING")
            self._current_phase = ExecutionPhase.PLANNING
            return
        
        print(f"📊 [DEBUG] Plan status: total={plan_status.total_items}, pending={plan_status.pending_items}, complete={plan_status.is_complete}")
        
        # Determine phase based on typed work plan state
        if plan_status.total_items == 0:
            # Empty plan - stay in planning
            print(f"📋 [DEBUG] Empty plan - staying in PLANNING")
            self._current_phase = ExecutionPhase.PLANNING
        elif plan_status.pending_items > 0:
            # Unassigned items - should be in allocation
            print(f"📋 [DEBUG] {plan_status.pending_items} pending items - going to ALLOCATION")
            self._current_phase = ExecutionPhase.ALLOCATION
        elif plan_status.in_progress_items > 0 or plan_status.waiting_items > 0:
            # Items executing or waiting for responses - monitor
            print(f"📋 [DEBUG] Items in progress/waiting - going to MONITORING")
            self._current_phase = ExecutionPhase.MONITORING
        elif plan_status.is_complete:
            # All items complete - synthesize
            print(f"📋 [DEBUG] Plan complete - going to SYNTHESIS")
            self._current_phase = ExecutionPhase.SYNTHESIS
        elif plan_status.has_local_ready:
            # Local items ready to execute
            print(f"📋 [DEBUG] Local items ready - going to EXECUTION")
            self._current_phase = ExecutionPhase.EXECUTION
        else:
            # Default to monitoring if unclear
            print(f"📋 [DEBUG] Unclear state - defaulting to MONITORING")
            self._current_phase = ExecutionPhase.MONITORING
            
        print(f"🔄 [DEBUG] _update_phase() - Final: {self._current_phase}")
    
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
        """Advance to the next phase and reset iteration counter."""
        phases = [
            ExecutionPhase.PLANNING,
            ExecutionPhase.ALLOCATION,
            ExecutionPhase.EXECUTION,
            ExecutionPhase.MONITORING,
            ExecutionPhase.SYNTHESIS
        ]
        
        current_idx = phases.index(self._current_phase)
        if current_idx < len(phases) - 1:
            self._current_phase = phases[current_idx + 1]
            self._phase_iterations = 0
    
    def _get_work_plan_status(self) -> Optional[WorkPlanStatus]:
        """
        Get current work plan status from phase context provider.
        
        Single Responsibility: Strategy only manages phases,
        node provides the context information needed via typed provider.
        
        Returns None if no context provider is available.
        """
        if not self._phase_context_provider:
            return None
        
        try:
            # Get typed context from provider
            phase_state = self._phase_context_provider.get_phase_context()
            return phase_state.work_plan_status
        except Exception as e:
            print(f"Error getting phase context: {e}")
            return None
    
    
    def _build_phase_prompt(self) -> str:
        """Build phase-specific system prompt using phase provider."""
        base_prompt = self.system_message or SystemPrompts.PLAN_AND_EXECUTE
        
        # Get concise phase guidance from provider
        try:
            phase_guidance = self._phase_provider.get_phase_guidance(self._current_phase)
            if phase_guidance:
                return f"{base_prompt}\n\n{phase_guidance}"
        except Exception as e:
            print(f"Error getting phase guidance: {e}")
        
        return base_prompt
