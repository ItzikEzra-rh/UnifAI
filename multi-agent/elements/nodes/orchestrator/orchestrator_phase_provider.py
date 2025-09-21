"""
Orchestrator-specific phase provider implementation.

Implements unified PhaseProvider interface with orchestrator-specific logic
for context, tools, and phase transitions.
"""

from typing import List, Dict, Set, Callable, Any
from elements.tools.common.base_tool import BaseTool
from elements.nodes.common.agent.unified_phase_provider import BasePhaseProvider
from elements.nodes.common.agent.constants import ExecutionPhase, ToolCategory, PhaseToolMapping
from elements.nodes.common.agent.phase_protocols import PhaseState, create_phase_state, create_work_plan_status
from elements.nodes.common.workload import WorkPlanService

# Forward declaration for AgentObservation
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..primitives import AgentObservation


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
    
    def __init__(
        self, 
        tools: List[BaseTool],
        get_workspace: Callable[[str], Any],
        node_uid: str,
        thread_id: str
    ):
        """
        Initialize orchestrator phase provider.
        
        Args:
            tools: All available tools for categorization
            get_workspace: Function to get workspace by thread_id
            node_uid: Node identifier
            thread_id: Current thread ID for context
        """
        super().__init__(tools)
        self._get_workspace = get_workspace
        self._node_uid = node_uid
        self._thread_id = thread_id
        self._tool_categories = self._categorize_tools(tools)
    
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
    
    def get_tools_for_phase(self, phase: ExecutionPhase) -> List[BaseTool]:
        """
        Get tools appropriate for the orchestrator's current phase.
        
        Uses tool categorization to filter tools based on phase requirements.
        """
        try:
            # Get categories for this phase using the abstract method
            phase_categories = self.get_phase_tool_categories(phase)
            
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
    
    def get_phase_tool_categories(self, phase: ExecutionPhase) -> Set[ToolCategory]:
        """
        Get tool categories allowed for orchestrator in a specific phase.
        
        Uses PhaseToolMapping to determine appropriate categories for each phase.
        
        Args:
            phase: The execution phase
            
        Returns:
            Set of tool categories allowed in this phase
        """
        return PhaseToolMapping.get_categories_for_phase(phase)
    
    def get_supported_phases(self) -> List[ExecutionPhase]:
        """
        Get phases supported by the orchestrator.
        
        Orchestrator supports the full plan-and-execute workflow:
        1. PLANNING - Create and structure work plans
        2. ALLOCATION - Assign work to local/remote execution  
        3. EXECUTION - Execute local work items
        4. MONITORING - Monitor progress and handle responses
        5. SYNTHESIS - Summarize results and create deliverables
        
        Returns:
            List of execution phases in orchestrator workflow order
        """
        return [
            ExecutionPhase.PLANNING,
            ExecutionPhase.ALLOCATION,
            ExecutionPhase.EXECUTION, 
            ExecutionPhase.MONITORING,
            ExecutionPhase.SYNTHESIS
        ]
    
    def validate_phase_transition(self, from_phase: ExecutionPhase, to_phase: ExecutionPhase) -> bool:
        """
        Validate orchestrator-specific phase transitions.
        
        Orchestrator has specific transition rules:
        - PLANNING can go to ALLOCATION or stay in PLANNING
        - ALLOCATION can go to EXECUTION, MONITORING, or back to PLANNING
        - EXECUTION typically goes to MONITORING
        - MONITORING can go to ALLOCATION, EXECUTION, or SYNTHESIS
        - SYNTHESIS is terminal (stays in SYNTHESIS)
        
        Args:
            from_phase: Current phase
            to_phase: Target phase
            
        Returns:
            True if transition is allowed for orchestrator workflow
        """
        # Define allowed transitions for orchestrator
        allowed_transitions = {
            ExecutionPhase.PLANNING: {
                ExecutionPhase.PLANNING,    # Stay in planning
                ExecutionPhase.ALLOCATION   # Move to allocation
            },
            ExecutionPhase.ALLOCATION: {
                ExecutionPhase.PLANNING,    # Back to planning
                ExecutionPhase.ALLOCATION,  # Stay in allocation  
                ExecutionPhase.EXECUTION,   # Move to execution
                ExecutionPhase.MONITORING   # Move to monitoring
            },
            ExecutionPhase.EXECUTION: {
                ExecutionPhase.EXECUTION,   # Stay in execution
                ExecutionPhase.MONITORING   # Move to monitoring
            },
            ExecutionPhase.MONITORING: {
                ExecutionPhase.ALLOCATION,  # Back to allocation
                ExecutionPhase.EXECUTION,   # Back to execution
                ExecutionPhase.MONITORING,  # Stay in monitoring
                ExecutionPhase.SYNTHESIS    # Move to synthesis
            },
            ExecutionPhase.SYNTHESIS: {
                ExecutionPhase.SYNTHESIS    # Terminal phase
            }
        }
        
        return to_phase in allowed_transitions.get(from_phase, set())
    
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
