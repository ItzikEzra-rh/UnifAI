"""
Orchestrator-specific phase provider implementation.

Implements unified PhaseProvider interface with orchestrator-specific logic
for context, tools, and phase transitions.
"""

from typing import List, Dict, Set
from elements.tools.common.base_tool import BaseTool
from elements.nodes.common.agent.unified_phase_provider import BasePhaseProvider
from elements.nodes.common.agent.constants import ExecutionPhase, ToolCategory, PhaseToolMapping
from elements.nodes.common.agent.phase_protocols import PhaseState, create_phase_state, create_work_plan_status
from elements.nodes.common.workload import WorkPlanService

# Forward declaration for AgentObservation
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..primitives import AgentObservation
    from .orchestrator_node import OrchestratorNode


class OrchestratorPhaseProvider(BasePhaseProvider):
    """
    Orchestrator-specific implementation of unified PhaseProvider.
    
    Encapsulates all orchestrator phase concerns:
    - Work plan context from WorkPlanService
    - Tool categorization based on phase
    - Phase transition logic based on work plan status
    - Integration with orchestrator node capabilities
    
    Follows SOLID principles:
    - Single Responsibility: Manages all orchestrator phase concerns
    - Open/Closed: Extensible through inheritance
    - Dependency Inversion: Depends on abstractions (WorkPlanService, etc.)
    """
    
    def __init__(self, node: 'OrchestratorNode', thread_id: str, tools: List[BaseTool]):
        """
        Initialize orchestrator phase provider.
        
        Args:
            node: Orchestrator node instance for workspace access
            thread_id: Current thread ID for context
            tools: All available tools for categorization
        """
        super().__init__(tools)
        self._node = node
        self._thread_id = thread_id
        self._tool_categories = self._categorize_tools(tools)
    
    def get_phase_context(self) -> PhaseState:
        """
        Get orchestrator-specific phase context.
        
        Provides rich context including work plan status and node information.
        """
        try:
            workspace = self._node.get_workspace(self._thread_id)
            service = WorkPlanService(workspace)
            status_summary = service.get_status_summary(self._node.uid)
            
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
                node_uid=self._node.uid
            )
            
        except Exception as e:
            print(f"Error getting orchestrator phase context: {e}")
            # Return minimal context on error
            return create_phase_state(
                thread_id=self._thread_id,
                node_uid=self._node.uid
            )
    
    def get_tools_for_phase(self, phase: ExecutionPhase) -> List[BaseTool]:
        """
        Get tools appropriate for the orchestrator's current phase.
        
        Uses tool categorization to filter tools based on phase requirements.
        """
        try:
            # Get categories for this phase
            phase_categories = PhaseToolMapping.get_categories_for_phase(phase)
            
            # Collect tools from relevant categories
            phase_tools = []
            for category in phase_categories:
                if category in self._tool_categories:
                    phase_tools.extend(self._tool_categories[category])
            
            print(f"🔧 [DEBUG] Phase {phase.value} tools: {len(phase_tools)} tools from categories {[c.value for c in phase_categories]}")
            return phase_tools
            
        except Exception as e:
            print(f"Error getting tools for phase {phase}: {e}")
            # Fallback to all tools
            return self._tools.copy()
    
    def decide_next_phase(
        self,
        *,
        current_phase: ExecutionPhase,
        phase_state: PhaseState,
        observations: List['AgentObservation']
    ) -> ExecutionPhase:
        """
        Decide next phase based on orchestrator-specific logic.
        
        Phase transition rules:
        - PLANNING: Move to ALLOCATION when plan exists
        - ALLOCATION: Move to EXECUTION when items are assigned
        - EXECUTION: Move to MONITORING when local work is done
        - MONITORING: Move to SYNTHESIS when all work is complete, or back to ALLOCATION/EXECUTION
        - SYNTHESIS: Stay in SYNTHESIS (terminal phase)
        """
        if not phase_state.work_plan_status:
            # No work plan context, stay in current phase
            return current_phase
        
        status = phase_state.work_plan_status
        
        if current_phase == ExecutionPhase.PLANNING:
            # Move to allocation if we have items to allocate
            if status.total_items > 0:
                return ExecutionPhase.ALLOCATION
            else:
                return ExecutionPhase.PLANNING  # Stay in planning
        
        elif current_phase == ExecutionPhase.ALLOCATION:
            # Move to execution if we have local work ready
            if status.has_local_ready:
                return ExecutionPhase.EXECUTION
            # Move to monitoring if we have remote work waiting
            elif status.has_remote_waiting:
                return ExecutionPhase.MONITORING
            else:
                return ExecutionPhase.ALLOCATION  # Stay in allocation
        
        elif current_phase == ExecutionPhase.EXECUTION:
            # Move to monitoring after execution attempts
            return ExecutionPhase.MONITORING
        
        elif current_phase == ExecutionPhase.MONITORING:
            # Check if work is complete
            if status.is_complete:
                return ExecutionPhase.SYNTHESIS
            # Go back to allocation if we have pending items
            elif status.pending_items > 0:
                return ExecutionPhase.ALLOCATION
            # Go back to execution if we have local ready items
            elif status.has_local_ready:
                return ExecutionPhase.EXECUTION
            else:
                return ExecutionPhase.MONITORING  # Stay in monitoring
        
        elif current_phase == ExecutionPhase.SYNTHESIS:
            # Terminal phase - stay here
            return ExecutionPhase.SYNTHESIS
        
        else:
            # Unknown phase, default to planning
            return ExecutionPhase.PLANNING
    
    def _categorize_tools(self, tools: List[BaseTool]) -> Dict[ToolCategory, List[BaseTool]]:
        """
        Categorize tools by their category for phase-based filtering.
        
        Args:
            tools: All available tools
            
        Returns:
            Dictionary mapping tool categories to tool lists
        """
        categorized = {}
        
        for tool in tools:
            # Get tool category (assuming tools have a category attribute or method)
            category = self._get_tool_category(tool)
            if category:
                if category not in categorized:
                    categorized[category] = []
                categorized[category].append(tool)
        
        return categorized
    
    def _get_tool_category(self, tool: BaseTool) -> ToolCategory:
        """
        Determine the category of a tool based on its name and type.
        
        Args:
            tool: Tool to categorize
            
        Returns:
            ToolCategory for the tool, or None if unknown
        """
        tool_name = tool.__class__.__name__.lower()
        
        # Workplan tools
        if any(keyword in tool_name for keyword in ['workplan', 'plan', 'create', 'update', 'mark', 'status']):
            return ToolCategory.WORKPLAN
        
        # Delegation tools
        elif any(keyword in tool_name for keyword in ['delegate', 'task', 'assign']):
            return ToolCategory.DELEGATION
        
        # IEM tools
        elif any(keyword in tool_name for keyword in ['message', 'send', 'iem']):
            return ToolCategory.IEM
        
        # Topology tools
        elif any(keyword in tool_name for keyword in ['topology', 'adjacent', 'node', 'capability']):
            return ToolCategory.TOPOLOGY
        
        # Workspace tools
        elif any(keyword in tool_name for keyword in ['workspace', 'file', 'read', 'write', 'search']):
            return ToolCategory.WORKSPACE
        
        # Summarization tools
        elif any(keyword in tool_name for keyword in ['summarize', 'summary', 'report']):
            return ToolCategory.SUMMARIZATION
        
        # Default to workspace for unknown tools
        else:
            return ToolCategory.WORKSPACE
