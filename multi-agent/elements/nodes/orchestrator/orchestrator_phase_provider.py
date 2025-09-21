"""
Orchestrator-specific phase provider implementation.

Uses clean Pydantic models and enums to define orchestrator phases professionally.
"""

from enum import Enum
from typing import List, Callable, Any
from elements.tools.common.base_tool import BaseTool
from elements.nodes.common.agent.unified_phase_provider import BasePhaseProvider
from elements.nodes.common.agent.phase_definition import PhaseSystem, PhaseDefinition
from elements.nodes.common.agent.phase_protocols import PhaseState, create_phase_state, create_work_plan_status
from elements.nodes.common.workload import WorkPlanService

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


class OrchestratorPhaseProvider(BasePhaseProvider):
    """
    Professional orchestrator phase provider using clean Pydantic models and enums.
    
    Defines orchestrator phases with proper separation of concerns:
    - Domain tools come from init parameter (orchestrator's capabilities)
    - Orchestration tools are built-in (work plan, delegation, etc.)
    - Phases are defined using enums (no hardcoding)
    """

    def __init__(
            self,
            domain_tools: List[BaseTool],
            get_workspace: Callable[[str], Any],
            get_adjacent_nodes: Callable[[], Any],
            send_task: Callable[..., Any],
            node_uid: str,
            thread_id: str
    ):
        """
        Initialize orchestrator phase provider.
        
        Args:
            domain_tools: Domain-specific tools that this orchestrator can use
            get_workspace: Function to get workspace by thread_id
            get_adjacent_nodes: Function to get adjacent nodes dict
            send_task: Function to send IEM tasks (dst_uid, task) -> packet_id
            node_uid: Node identifier
            thread_id: Current thread ID for context
        """
        self._get_workspace = get_workspace
        self._get_adjacent_nodes = get_adjacent_nodes
        self._send_task = send_task
        self._node_uid = node_uid
        self._thread_id = thread_id
        self._domain_tools = domain_tools

        super().__init__(domain_tools)  # This calls _create_phase_system()

    def _create_phase_system(self) -> PhaseSystem:
        """
        Create the orchestrator phase system.
        
        Tool separation:
        - Built-in tools: Initialize here (workplan, delegation, topology, etc.)
        - Domain tools: Already initialized, passed from constructor (execution tools)
        """
        # Accessors required by tools
        get_ws = lambda: self._get_workspace(self._thread_id)
        get_tid = lambda: self._thread_id
        get_uid = lambda: self._node_uid

        # Initialize built-in orchestration tools with correct callables
        create_plan_tool = CreateOrUpdateWorkPlanTool(
            get_workspace=get_ws,
            get_thread_id=get_tid,
            get_owner_uid=get_uid
        )
        assign_tool = AssignWorkItemTool(
            get_workspace=get_ws,
            get_owner_uid=get_uid
        )
        mark_status_tool = MarkWorkItemStatusTool(
            get_workspace=get_ws,
            get_owner_uid=get_uid
        )
        summarize_tool = SummarizeWorkPlanTool(
            get_workspace=get_ws,
            get_owner_uid=get_uid
        )
        delegate_tool = DelegateTaskTool(
            send_task=self._send_task,
            get_owner_uid=get_uid,
            get_workspace=get_ws,
            check_adjacency=lambda uid: uid in (self._get_adjacent_nodes() or {})
        )
        list_nodes_tool = ListAdjacentNodesTool(get_adjacent_nodes=self._get_adjacent_nodes)
        get_node_card_tool = GetNodeCardTool(get_adjacent_nodes=self._get_adjacent_nodes)

        # Create phase definitions directly in execution order (no interim configs)
        domain_tools_list = list(self._domain_tools)

        planning_phase = PhaseDefinition(
            name=OrchestratorPhase.PLANNING.value,
            description="Create detailed work plan with dependencies and task breakdown",
            tools=[create_plan_tool, list_nodes_tool, get_node_card_tool] + domain_tools_list,
            guidance=(
                "PHASE: PLANNING - Create detailed work plan with dependencies. "
                "Break down tasks logically. Don't execute or delegate yet."
            )
        )

        allocation_phase = PhaseDefinition(
            name=OrchestratorPhase.ALLOCATION.value,
            description="Assign work items to appropriate nodes and delegate tasks",
            tools=[assign_tool, delegate_tool, list_nodes_tool, get_node_card_tool, create_plan_tool],
            guidance=(
                "PHASE: ALLOCATION - Assign work items to appropriate nodes. "
                "Use adjacency info to delegate. Don't execute local work yet."
            )
        )

        execution_phase = PhaseDefinition(
            name=OrchestratorPhase.EXECUTION.value,
            description="Execute local work items using domain capabilities",
            tools=[create_plan_tool] + domain_tools_list,
            guidance=(
                "PHASE: EXECUTION - Execute local work items only. "
                "Don't modify plan structure or delegate new work."
            )
        )

        monitoring_phase = PhaseDefinition(
            name=OrchestratorPhase.MONITORING.value,
            description="Interpret responses and manage work item lifecycle",
            tools=[mark_status_tool, delegate_tool, list_nodes_tool, create_plan_tool],
            guidance=(
                "PHASE: MONITORING - Interpret responses and decide next steps. "
                "Respect retry limits. Mark status only when certain about outcome."
            )
        )

        synthesis_phase = PhaseDefinition(
            name=OrchestratorPhase.SYNTHESIS.value,
            description="Summarize completed work and produce final deliverables",
            tools=[summarize_tool, create_plan_tool],
            guidance=(
                "PHASE: SYNTHESIS - Summarize completed work and produce final deliverables. "
                "Focus on results and outputs."
            )
        )

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
            workspace = self._get_workspace(self._thread_id)
            service = WorkPlanService(workspace)
            status_summary = service.get_status_summary(self._node_uid)

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

    def decide_next_phase(
            self,
            current_phase: str,
            context: PhaseState,
            observations: List[Any]  # Not used but required by protocol
    ) -> str:
        """
        Decide next phase based on orchestrator-specific logic using enums.
        
        Professional phase transition rules using OrchestratorPhase enum.
        """
        if not context.work_plan_status:
            return OrchestratorPhase.PLANNING.value  # No work plan, start planning

        status = context.work_plan_status

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
            # Move to monitoring if we have remote work waiting
            elif status.has_remote_waiting:
                return OrchestratorPhase.MONITORING.value
            else:
                return OrchestratorPhase.ALLOCATION.value  # Stay in allocation

        elif current_phase_enum == OrchestratorPhase.EXECUTION:
            # Move to monitoring after execution attempts
            return OrchestratorPhase.MONITORING.value

        elif current_phase_enum == OrchestratorPhase.MONITORING:
            # Check if work is complete
            if status.is_complete:
                return OrchestratorPhase.SYNTHESIS.value
            # Go back to allocation if we have pending items
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
