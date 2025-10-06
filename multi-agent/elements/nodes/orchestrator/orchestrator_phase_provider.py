"""
Orchestrator-specific phase provider implementation.

Uses clean Pydantic models and enums to define orchestrator phases professionally.
"""

from enum import Enum
from typing import List, Callable, Any, Optional
from elements.tools.common.base_tool import BaseTool
from elements.nodes.common.agent.phases.unified_phase_provider import PhaseProvider
from elements.nodes.common.agent.phases.phase_definition import PhaseSystem, PhaseDefinition
from elements.nodes.common.agent.phases.phase_protocols import PhaseState, create_phase_state, create_work_plan_status
from elements.nodes.common.agent.phases.models import PhaseValidationContext
from .phases.models import PhaseIterationLimits, PhaseIterationState
from .phases.validators import (
    AllocationValidator, PlanningValidator, ExecutionValidator, 
    MonitoringValidator, SynthesisValidator
)

# Built-in orchestration tools
from elements.tools.builtin.workplan.create_or_update import CreateOrUpdateWorkPlanTool
from elements.tools.builtin.workplan.assign_item import AssignWorkItemTool
from elements.tools.builtin.workplan.mark_status import MarkWorkItemStatusTool
from elements.tools.builtin.workplan.summarize import SummarizeWorkPlanTool
from elements.tools.builtin.delegation.delegate_task import DelegateTaskTool
from elements.tools.builtin.topology.list_adjacent import ListAdjacentNodesTool
from elements.tools.builtin.topology.get_node_card import GetNodeCardTool


class OrchestratorPhase(Enum):
    """
    Orchestrator execution phases.
    
    Defines the complete orchestrator workflow in execution order.
    """
    PLANNING = "planning"
    ALLOCATION = "allocation"
    EXECUTION = "execution"
    MONITORING = "monitoring"
    SYNTHESIS = "synthesis"

    @classmethod
    def get_execution_order(cls) -> List['OrchestratorPhase']:
        """Get phases in their natural execution order."""
        return [
            cls.PLANNING,
            cls.ALLOCATION,
            cls.EXECUTION,
            cls.MONITORING,
            cls.SYNTHESIS
        ]

    @classmethod
    def get_phase_names(cls) -> List[str]:
        """Get phase names as strings in execution order."""
        return [phase.value for phase in cls.get_execution_order()]


class OrchestratorPhaseProvider(PhaseProvider):
    """
    Professional orchestrator phase provider using clean Pydantic models and enums.
    
    Defines orchestrator phases with proper separation of concerns:
    - Domain tools come from init parameter (orchestrator's capabilities)
    - Orchestration tools are built-in (work plan, delegation, etc.)
    - Phases are defined using enums (no hardcoding)
    - Iteration limits managed via Pydantic models in PhaseDefinition
    
    DESIGN NOTE:
    The phase provider receives already-filtered adjacent nodes from the orchestrator.
    It does NOT know about delegation policies - that's the orchestrator's responsibility.
    This ensures clean separation: orchestrator decides WHO is adjacent, provider uses it.
    """

    def __init__(
            self,
            domain_tools: List[BaseTool],
            get_adjacent_nodes: Callable[[], Any],
            send_task: Callable[..., Any],
            node_uid: str,
            thread_id: str,
            get_workload_service: Callable[[], Any],
            iteration_limits: Optional[PhaseIterationLimits] = None
    ):
        """
        Initialize orchestrator phase provider.
        
        Args:
            domain_tools: Domain-specific tools that this orchestrator can use
            get_adjacent_nodes: Function to get adjacent nodes (already filtered by orchestrator)
            send_task: Function to send IEM tasks (dst_uid, task) -> packet_id
            node_uid: Node identifier
            thread_id: Current thread ID for context
            get_workload_service: Function to get workload service
            iteration_limits: Custom iteration limits configuration (optional)
        
        Note:
            get_adjacent_nodes should return nodes that the orchestrator has already
            filtered according to its delegation policy. The provider doesn't apply
            any additional filtering - it trusts what the orchestrator gives it.
        """
        self._get_adjacent_nodes = get_adjacent_nodes
        self._send_task = send_task
        self._node_uid = node_uid
        self._thread_id = thread_id
        self._domain_tools = domain_tools
        self._get_workload_service = get_workload_service
        
        # Configure iteration limits using Pydantic model
        self._iteration_limits = iteration_limits or PhaseIterationLimits()
        
        # Track iteration state using Pydantic model
        self._iteration_state = PhaseIterationState()
        
        # Private: Cascade safety limit
        self._max_cascade_transitions = 10

        super().__init__(domain_tools)  # This calls _create_phase_system()
    
    def _get_current_thread(self):
        """Get current thread for delegation context."""
        workload_service = self._get_workload_service()
        return workload_service.get_thread(self._thread_id)

    def _increment_phase_iteration(self, phase_name: str) -> None:
        """
        Private: Increment iteration count for the given phase.
        
        Args:
            phase_name: Name of the phase to increment
        """
        self._iteration_state = self._iteration_state.increment(phase_name)
        current = self._iteration_state.get_count(phase_name)
        limit = self._iteration_limits.get_limit(phase_name)
        print(f"🔢 [ORCHESTRATOR] Phase {phase_name}: {current}/{limit} iterations")

    def _is_phase_limit_exceeded(self, phase_name: str) -> bool:
        """
        Private: Check if phase iteration limit is exceeded.
        
        Args:
            phase_name: Name of the phase to check
            
        Returns:
            True if limit exceeded, False otherwise
        """
        return self._iteration_state.is_exceeded(phase_name, self._iteration_limits)

    def _reset_phase_iteration(self, phase_name: str) -> None:
        """
        Private: Reset iteration count for the given phase.
        
        Args:
            phase_name: Name of the phase to reset
        """
        old_count = self._iteration_state.get_count(phase_name)
        self._iteration_state = self._iteration_state.reset(phase_name)
        print(f"🔄 [ORCHESTRATOR] Reset {phase_name}: {old_count} → 0")

    def _create_phase_system(self) -> PhaseSystem:
        """
        Create the orchestrator phase system.
        
        Tool separation:
        - Built-in tools: Initialize here (workplan, delegation, topology, etc.)
        - Domain tools: Already initialized, passed from constructor (execution tools)
        
        Adjacent Nodes:
        - Phase provider receives already-filtered adjacent nodes from orchestrator
        - No policy logic here - orchestrator has already applied its delegation policy
        - Provider simply uses the nodes it's given
        """
        # Clean SOLID dependencies
        get_tid = lambda: self._thread_id
        get_uid = lambda: self._node_uid

        # Get adjacent nodes (already filtered by orchestrator)
        adjacent_nodes = self._get_adjacent_nodes()

        # Initialize built-in orchestration tools with clean dependencies
        create_plan_tool = CreateOrUpdateWorkPlanTool(
            get_thread_id=get_tid,
            get_owner_uid=get_uid,
            get_workload_service=self._get_workload_service
        )
        assign_tool = AssignWorkItemTool(
            get_thread_id=get_tid,
            get_owner_uid=get_uid,
            get_workload_service=self._get_workload_service
        )
        mark_status_tool = MarkWorkItemStatusTool(
            get_thread_id=get_tid,
            get_owner_uid=get_uid,
            get_workload_service=self._get_workload_service
        )
        summarize_tool = SummarizeWorkPlanTool(
            get_thread_id=get_tid,
            get_owner_uid=get_uid,
            get_workload_service=self._get_workload_service
        )
        
        # Tools use the adjacent nodes provided by orchestrator (already filtered)
        delegate_tool = DelegateTaskTool(
            send_task=self._send_task,
            get_owner_uid=get_uid,
            get_current_thread=lambda: self._get_current_thread(),
            get_thread_service=lambda: self._get_workload_service().get_thread_service(),
            get_workspace_service=lambda: self._get_workload_service().get_workspace_service(),
            check_adjacency=lambda uid: uid in adjacent_nodes  # Simple membership check
        )
        list_nodes_tool = ListAdjacentNodesTool(
            get_adjacent_nodes=self._get_adjacent_nodes  # Uses orchestrator-provided nodes
        )
        get_node_card_tool = GetNodeCardTool(
            get_adjacent_nodes=self._get_adjacent_nodes  # Uses orchestrator-provided nodes
        )

        # Create phase definitions directly in execution order (no interim configs)
        domain_tools_list = list(self._domain_tools)

        # Create validators
        planning_validator = PlanningValidator()
        allocation_validator = AllocationValidator()
        execution_validator = ExecutionValidator()
        monitoring_validator = MonitoringValidator()
        synthesis_validator = SynthesisValidator()

        planning_phase = PhaseDefinition(
            name=OrchestratorPhase.PLANNING.value,
            description="Create detailed work plan with dependencies and task breakdown",
            tools=[create_plan_tool, list_nodes_tool, get_node_card_tool],
            guidance=(
                "PHASE: PLANNING - Create detailed work plan with dependencies. "
                "Break down tasks logically. Don't execute or delegate yet."
            ),
            max_iterations=self._iteration_limits.planning
        )
        planning_phase.add_validator(planning_validator)

        allocation_phase = PhaseDefinition(
            name=OrchestratorPhase.ALLOCATION.value,
            description="Assign work items to appropriate nodes and delegate tasks",
            tools=[assign_tool, delegate_tool, list_nodes_tool, get_node_card_tool, create_plan_tool],
            guidance=(
                "PHASE: ALLOCATION - Assign work items to appropriate nodes. "
                "Use adjacency info to delegate. Don't execute local work yet."
            ),
            max_iterations=self._iteration_limits.allocation
        )
        allocation_phase.add_validator(allocation_validator)

        execution_phase = PhaseDefinition(
            name=OrchestratorPhase.EXECUTION.value,
            description="Execute local work items using domain capabilities",
            tools=[create_plan_tool] + domain_tools_list,
            guidance=(
                "PHASE: EXECUTION - Execute local work items only. "
                "Don't modify plan structure or delegate new work."
            ),
            max_iterations=self._iteration_limits.execution
        )
        execution_phase.add_validator(execution_validator)

        monitoring_phase = PhaseDefinition(
            name=OrchestratorPhase.MONITORING.value,
            description="Interpret responses and manage work item lifecycle",
            tools=[mark_status_tool, delegate_tool, list_nodes_tool, create_plan_tool],
            guidance=(
                "PHASE: MONITORING - Interpret responses and decide next steps. "
                "Respect retry limits. Mark status only when certain about outcome."
            ),
            max_iterations=self._iteration_limits.monitoring
        )
        monitoring_phase.add_validator(monitoring_validator)

        synthesis_phase = PhaseDefinition(
            name=OrchestratorPhase.SYNTHESIS.value,
            description="Summarize completed work and produce final deliverables",
            tools=[summarize_tool],  # ✅ ONLY summarize - NO plan modification in Synthesis!
            guidance=(
                "PHASE: SYNTHESIS - Summarize completed work and produce final deliverables. "
                "Focus on results and outputs. Work plan is complete - do NOT add new items."
            ),
            max_iterations=self._iteration_limits.synthesis
        )
        synthesis_phase.add_validator(synthesis_validator)

        phases = [
            planning_phase,
            allocation_phase,
            execution_phase,
            monitoring_phase,
            synthesis_phase
        ]

        # Create the complete phase system
        return PhaseSystem(
            name="orchestrator",
            description="Complete orchestrator workflow: " + " → ".join(OrchestratorPhase.get_phase_names()),
            phases=phases
        )

    def get_phase_context(self) -> PhaseState:
        """
        Get orchestrator-specific phase context.
        
        Provides rich context including work plan status and node information.
        """
        try:
            workload_service = self._get_workload_service()
            workspace_service = workload_service.get_workspace_service()
            status_summary = workspace_service.get_work_plan_status(self._thread_id, self._node_uid)

            # Convert to PhaseState format
            work_plan_status = create_work_plan_status(
                total_items=status_summary.total_items,
                pending_items=status_summary.pending_items,
                in_progress_items=status_summary.in_progress_items,
                waiting_items=status_summary.waiting_items,
                done_items=status_summary.done_items,
                failed_items=status_summary.failed_items,
                blocked_items=status_summary.blocked_items,
                has_local_ready=status_summary.has_local_ready,
                has_remote_waiting=status_summary.has_remote_waiting,
                has_responses=status_summary.has_responses,
                is_complete=status_summary.is_complete
            )

            return create_phase_state(
                work_plan_status=work_plan_status,
                thread_id=self._thread_id,
                node_uid=self._node_uid
            )

        except Exception as e:
            print(f"Error getting orchestrator phase context: {e}")
            # Return minimal context on error
            return create_phase_state(
                thread_id=self._thread_id,
                node_uid=self._node_uid
            )

    def get_initial_phase(self) -> str:
        """
        Get the initial phase for orchestration.
        
        Orchestrator always starts with planning.
        """
        return OrchestratorPhase.PLANNING.value
    
    def is_terminal_phase(self, phase_name: str) -> bool:
        """
        Check if phase is terminal.
        
        SYNTHESIS is the only terminal phase - represents workflow completion.
        Other phases may stay in themselves temporarily (processing, waiting)
        but will eventually transition.
        
        Args:
            phase_name: Phase name to check
            
        Returns:
            True if terminal (SYNTHESIS), False otherwise
        """
        return phase_name == OrchestratorPhase.SYNTHESIS.value
    
    def update_phase(
        self,
        current_phase: str,
        observations: List[Any]
    ) -> str:
        """
        Update phase with orchestrator's internal cascade logic.
        
        PRIVATE IMPLEMENTATION:
        - Increment iteration
        - Cascade until stable
        - Reset iteration on transition
        - Safety limits and cycle detection
        
        Strategy doesn't see any of this - just gets final phase.
        
        Args:
            current_phase: Current phase name
            observations: Recent observations from execution
            
        Returns:
            Final stable phase name
        """
        # Increment iteration for current phase
        self._increment_phase_iteration(current_phase)
        
        # Get initial context
        context = self.get_phase_context()
        
        # Private cascade logic (internal to orchestrator)
        final_phase = self._cascade_to_stable(current_phase, context, observations)
        
        # Reset iteration if phase changed
        if final_phase != current_phase:
            self._reset_phase_iteration(current_phase)
        
        return final_phase
    
    def _cascade_to_stable(
        self,
        current_phase: str,
        context: PhaseState,
        observations: List[Any]
    ) -> str:
        """
        Private: Cascade transitions until reaching stable phase.
        
        Keeps calling decide_next_phase() until phase is stable.
        Includes safety mechanisms: max transitions, cycle detection, validation.
        
        Args:
            current_phase: Starting phase
            context: Current phase state
            observations: Recent observations
            
        Returns:
            Final stable phase
        """
        transitions = [current_phase]
        visited = {current_phase}
        current = current_phase
        
        for cascade_num in range(self._max_cascade_transitions):
            # Decide next phase
            next_phase = self.decide_next_phase(current, context, observations)
            
            # Stable - done
            if next_phase == current:
                self._log_cascade(transitions, cascade_num, 'stable')
                return current
            
            # Validate transition
            if not self.validate_transition(current, next_phase):
                self._log_cascade(transitions, cascade_num, 'invalid')
                return current
            
            # Cycle detection
            if next_phase in visited:
                self._log_cascade(transitions + [next_phase], cascade_num, 'cycle')
                return current
            
            # Continue cascade
            transitions.append(next_phase)
            visited.add(next_phase)
            current = next_phase
            
            # Refresh context for next iteration
            context = self.get_phase_context()
        
        # Max transitions reached
        self._log_cascade(transitions, self._max_cascade_transitions, 'max_transitions')
        return current
    
    def _log_cascade(self, transitions: List[str], count: int, reason: str) -> None:
        """
        Private: Log cascade results.
        
        Args:
            transitions: List of phases visited
            count: Number of transitions
            reason: Why cascade stopped
        """
        if count == 0:
            return  # No cascade happened, no log needed
        
        path = " → ".join(transitions)
        
        if reason == 'stable':
            print(f"🎯 [ORCHESTRATOR] Phase cascade: {path} ({count} steps)")
        elif reason == 'cycle':
            print(f"⚠️ [ORCHESTRATOR] Cycle detected: {path}")
        elif reason == 'max_transitions':
            print(f"⚠️ [ORCHESTRATOR] Max transitions ({count}): {path}")
        elif reason == 'invalid':
            print(f"⚠️ [ORCHESTRATOR] Invalid transition: {path}")

    def decide_next_phase(
            self,
            current_phase: str,
            context: PhaseState,
            observations: List[Any]  # Not used but required by protocol
    ) -> str:
        """
        Decide next phase based on orchestrator-specific logic using enums.
        
        Professional phase transition rules using OrchestratorPhase enum.
        Enforces iteration limits to prevent infinite loops.
        """
        print(f"📍 [DEBUG] decide_next_phase() - current: {current_phase}")
        
        # Handle None context gracefully
        if not context or not context.work_plan_status:
            return OrchestratorPhase.PLANNING.value  # No context or work plan, start planning

        status = context.work_plan_status
        print(f"📊 [DEBUG] Work plan status: total={status.total_items if status else 'None'}")
        
        # Check iteration limits first
        if self._is_phase_limit_exceeded(current_phase):
            print(f"⚠️ [ORCHESTRATOR] Phase {current_phase} exceeded iteration limit")
            return self._handle_phase_limit_exceeded(current_phase, status)

        # Convert current_phase to enum for type-safe comparison
        try:
            current_phase_enum = OrchestratorPhase(current_phase)
        except ValueError:
            # Unknown phase, default to planning
            return OrchestratorPhase.PLANNING.value

        # Phase transition logic using enums
        if current_phase_enum == OrchestratorPhase.PLANNING:
            # Move to allocation if we have items to allocate
            if status.total_items > 0:
                return OrchestratorPhase.ALLOCATION.value
            else:
                return OrchestratorPhase.PLANNING.value  # Stay in planning

        elif current_phase_enum == OrchestratorPhase.ALLOCATION:
            # Move to execution if we have local work ready
            if status.has_local_ready:
                return OrchestratorPhase.EXECUTION.value
            # Move to monitoring if we have responses to interpret
            elif status.has_responses:
                return OrchestratorPhase.MONITORING.value
            # If just waiting (no responses yet), stay in allocation (will finish and wait for graph)
            elif status.has_remote_waiting:
                return OrchestratorPhase.ALLOCATION.value  # Stay → finish
            else:
                return OrchestratorPhase.ALLOCATION.value  # Stay in allocation

        elif current_phase_enum == OrchestratorPhase.EXECUTION:
            # Move to monitoring after execution attempts
            return OrchestratorPhase.MONITORING.value

        elif current_phase_enum == OrchestratorPhase.MONITORING:
            # Check if work is complete
            if status.is_complete:
                return OrchestratorPhase.SYNTHESIS.value
            # PRIORITY: Stay in monitoring if we still have responses to interpret
            # (Process responses BEFORE transitioning to handle new pending work)
            elif status.has_responses:
                return OrchestratorPhase.MONITORING.value
            # Go back to allocation if we have pending items (and no responses)
            elif status.pending_items > 0:
                return OrchestratorPhase.ALLOCATION.value
            # Go back to execution if we have local ready items
            elif status.has_local_ready:
                return OrchestratorPhase.EXECUTION.value
            else:
                return OrchestratorPhase.MONITORING.value  # Stay in monitoring

        elif current_phase_enum == OrchestratorPhase.SYNTHESIS:
            # Terminal phase - stay here
            return OrchestratorPhase.SYNTHESIS.value

        else:
            # Fallback (should not reach here with enum validation above)
            return OrchestratorPhase.PLANNING.value
    
    def _handle_phase_limit_exceeded(self, current_phase: str, status) -> str:
        """
        Private: Handle when a phase exceeds its iteration limit.
        
        Args:
            current_phase: Phase that exceeded limit
            status: Current work plan status
            
        Returns:
            Next phase to transition to (or synthesis for terminal)
        """
        print(f"🚨 [ORCHESTRATOR] Phase limit exceeded for {current_phase}")
        
        try:
            current_phase_enum = OrchestratorPhase(current_phase)
        except ValueError:
            # Unknown phase, go to synthesis
            return OrchestratorPhase.SYNTHESIS.value
        
        # Phase-specific limit handling
        if current_phase_enum == OrchestratorPhase.PLANNING:
            # If planning stuck, try allocation anyway (maybe partial plan is enough)
            if status and status.total_items > 0:
                return OrchestratorPhase.ALLOCATION.value
            else:
                # No plan at all - terminal failure, go to synthesis
                return OrchestratorPhase.SYNTHESIS.value
                
        elif current_phase_enum == OrchestratorPhase.ALLOCATION:
            # If allocation stuck, try execution with what we have
            if status and status.has_local_ready:
                return OrchestratorPhase.EXECUTION.value
            else:
                # Skip to monitoring or synthesis
                return OrchestratorPhase.MONITORING.value
                
        elif current_phase_enum == OrchestratorPhase.EXECUTION:
            # If execution stuck, move to monitoring
            return OrchestratorPhase.MONITORING.value
            
        elif current_phase_enum == OrchestratorPhase.MONITORING:
            # If monitoring stuck (waiting too long), force synthesis
            return OrchestratorPhase.SYNTHESIS.value
            
        else:
            # For synthesis or unknown phases, stay in synthesis
            return OrchestratorPhase.SYNTHESIS.value

    def _build_validation_context(self, phase_name: str) -> PhaseValidationContext:
        """
        Build orchestrator-specific validation context.
        
        Extends base context with orchestrator-specific data:
        - Work plan for validation
        - Adjacent nodes for assignment validation
        
        Args:
            phase_name: Name of the phase to validate
            
        Returns:
            PhaseValidationContext with orchestrator-specific data
        """
        # Get base phase state
        phase_state = self.get_phase_context()
        
        # Enrich with orchestrator-specific data
        try:
            from graph.models import AdjacentNodes
            
            workload_service = self._get_workload_service()
            workspace_service = workload_service.get_workspace_service()
            plan = workspace_service.load_work_plan(self._thread_id, self._node_uid)
            
            # Get adjacent nodes (already an AdjacentNodes model)
            adjacent_nodes = self._get_adjacent_nodes()
            
            return PhaseValidationContext(
                phase_state=phase_state,
                thread_id=self._thread_id,
                node_uid=self._node_uid,
                plan=plan,
                adjacent_nodes=adjacent_nodes
            )
        except Exception as e:
            print(f"Validation context error: {e}")
            # Return minimal context on error
            return PhaseValidationContext(
                phase_state=phase_state,
                thread_id=self._thread_id,
                node_uid=self._node_uid
            )
