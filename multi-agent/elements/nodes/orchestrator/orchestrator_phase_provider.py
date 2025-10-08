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
# SummarizeWorkPlanTool removed - work plan now provided via dynamic context
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
        # Note: SummarizeWorkPlanTool removed - work plan is now provided via dynamic context
        
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
            description="Create or update work plan with dependencies and task breakdown",
            tools=[create_plan_tool, list_nodes_tool, get_node_card_tool],
            guidance=(
                "PHASE: PLANNING - Create or update work plan based on new request.\n\n"
                "MULTI-REQUEST WORKFLOW (Same Thread):\n"
                "1. FIRST: Check 'Current Work Plan' section above to see if work plan already exists\n\n"
                "2. IF NO PLAN EXISTS:\n"
                "   Create comprehensive work plan using CreateOrUpdateWorkPlanTool:\n"
                "   - Break down request into specific, actionable work items\n"
                "   - Give each item a descriptive snake_case ID (e.g., 'research_trends', 'analyze_data')\n"
                "   - Write clear title and detailed description for each item\n"
                "   - Identify dependencies between items (which must complete before others)\n"
                "   - Determine execution type:\n"
                "     * LOCAL: Tasks you can execute yourself (with or without domain tools)\n"
                "     * REMOTE: Tasks requiring specialized agents (check with ListAdjacentNodesTool)\n"
                "   - Write comprehensive summary describing overall goal\n"
                "   - Start simple: 3-5 well-defined items better than 20 vague ones\n\n"
                "3. IF PLAN EXISTS:\n"
                "   - Review existing items (DONE/IN_PROGRESS/PENDING/FAILED)\n"
                "   - Understand what work has been completed\n"
                "   - Determine how new request relates to existing work\n"
                "   - Update plan accordingly (add new items, update descriptions, adjust dependencies)\n\n"
                "HANDLING EXISTING WORK PLANS:\n"
                "- NEW independent work → Add new items to existing plan\n"
                "- FOLLOW-UP on completed work → Add items that depend on DONE items\n"
                "- CLARIFICATION → May not need new items, just check existing results\n"
                "- CONTINUATION → Add items that build on IN_PROGRESS work\n"
                "- RE-DO failed work → Can reuse failed item IDs with updated approach\n\n"
                "WORK ITEM BEST PRACTICES:\n"
                "- Dependencies: Use item IDs in dependencies list (e.g., dependencies: ['research_trends'])\n"
                "- Specificity: 'Research top 5 AI trends in 2024' > 'Research AI'\n"
                "- Granularity: Break complex tasks into smaller steps\n"
                "- Logical order: Arrange items in execution sequence\n\n"
                "IMPORTANT:\n"
                "- CreateOrUpdateWorkPlanTool preserves runtime state (status, results, etc.)\n"
                "- Existing DONE items stay DONE - don't recreate them\n"
                "- Use dependencies to link new work to completed items\n"
                "- Summary should reflect cumulative goals, not just new request\n"
                "- Focus on planning only - execution and delegation happen in later phases"
            ),
            max_iterations=self._iteration_limits.planning
        )
        planning_phase.add_validator(planning_validator)

        allocation_phase = PhaseDefinition(
            name=OrchestratorPhase.ALLOCATION.value,
            description="Assign work items to appropriate nodes and delegate tasks",
            tools=[assign_tool, delegate_tool, list_nodes_tool, get_node_card_tool, create_plan_tool],
            guidance=(
                "PHASE: ALLOCATION - Assign REMOTE work items to appropriate agents and delegate tasks.\n\n"
                "WORKFLOW:\n"
                "1. Review work plan for PENDING items with kind=REMOTE\n"
                "2. For each REMOTE item:\n"
                "   a. Use ListAdjacentNodesTool to see available agents\n"
                "   b. Use GetNodeCardTool to understand agent capabilities\n"
                "   c. Choose best agent based on task requirements and capabilities\n"
                "   d. Use AssignWorkItemTool to assign item to chosen agent\n"
                "   e. Use DelegateTaskTool to send task (MUST include work_item_id)\n"
                "3. Skip LOCAL items (handled in EXECUTION phase)\n\n"
                "ASSIGNMENT STRATEGY:\n"
                "- Match task requirements to agent specialization\n"
                "  * Research tasks → research_agent\n"
                "  * Jira operations → jira_agent\n"
                "  * Confluence queries → confluence_agent\n"
                "  * Analysis/reasoning → reasoning_agent\n"
                "- Check agent is in adjacency list (can't delegate to non-adjacent nodes)\n"
                "- One work item → One agent (no multi-assignment yet)\n"
                "- Consider agent capabilities from GetNodeCardTool\n\n"
                "DELEGATION COORDINATION:\n"
                "- CRITICAL: Always assign BEFORE delegate\n"
                "  1. AssignWorkItemTool(item_id, agent_uid) - marks assigned_uid\n"
                "  2. DelegateTaskTool(dst_uid, content, work_item_id) - creates child thread\n"
                "- MUST include work_item_id in DelegateTaskTool (enables response tracking)\n"
                "- Child thread created automatically (context for agent)\n"
                "- Correlation ID tracked for linking responses back to work item\n\n"
                "WHAT TO DELEGATE:\n"
                "- Only REMOTE items (kind=REMOTE)\n"
                "- Only PENDING or ready items (dependencies satisfied)\n"
                "- Include clear instructions in task content\n"
                "- Include context and expected deliverables\n\n"
                "IMPORTANT:\n"
                "- Don't execute LOCAL items here - wait for EXECUTION phase\n"
                "- Don't skip REMOTE items - all must be delegated\n"
                "- Incomplete delegation → Infinite loop risk (validator catches this)\n"
                "- Status changes: PENDING → IN_PROGRESS (remote) after delegation"
            ),
            max_iterations=self._iteration_limits.allocation
        )
        allocation_phase.add_validator(allocation_validator)

        execution_phase = PhaseDefinition(
            name=OrchestratorPhase.EXECUTION.value,
            description="Execute local work items using domain capabilities",
            tools=[create_plan_tool, mark_status_tool] + domain_tools_list,
            guidance=(
                "PHASE: EXECUTION - Execute LOCAL work items directly or using domain tools.\n\n"
                "WORKFLOW:\n"
                "1. Identify PENDING items with kind=LOCAL\n"
                "2. Check dependencies are satisfied (all dependencies must be DONE)\n"
                "3. For each ready LOCAL item:\n"
                "   a. Review item.description for requirements and deliverables\n"
                "   b. Determine execution approach:\n"
                "      * WITH domain tools: Use appropriate tool(s) for the task\n"
                "      * WITHOUT domain tools: Execute directly using your reasoning/knowledge\n"
                "   c. Execute the work\n"
                "   d. Capture results, outputs, or insights\n"
                "   e. Use MarkWorkItemStatusTool to mark DONE or FAILED\n"
                "4. Store results for later synthesis\n\n"
                "EXECUTION STRATEGY:\n"
                "- Read full item description to understand requirements\n"
                "- Check if domain tools are available and appropriate\n"
                "- If tools available → Use them for specialized tasks\n"
                "- If NO tools available → Execute directly:\n"
                "  * Use your reasoning and knowledge\n"
                "  * Perform analysis, synthesis, or planning tasks\n"
                "  * Generate insights, summaries, or recommendations\n"
                "  * Create structured outputs based on requirements\n"
                "- Execute step-by-step if complex task\n"
                "- Capture all relevant outputs and intermediate results\n"
                "- Verify work meets requirements before marking DONE\n\n"
                "MARKING STATUS:\n"
                "- SUCCESS: MarkWorkItemStatusTool(item_id, status='done', notes='Brief summary of results')\n"
                "  * Work completed successfully\n"
                "  * Requirements satisfied\n"
                "  * Results captured\n"
                "- FAILURE: MarkWorkItemStatusTool(item_id, status='failed', notes='Error description')\n"
                "  * Tool errors or exceptions\n"
                "  * Cannot complete due to missing data/resources\n"
                "  * Requirements cannot be satisfied\n"
                "- Store detailed results in notes for synthesis phase\n\n"
                "RESULT HANDLING:\n"
                "- Capture outputs: data, calculations, analysis results, insights\n"
                "- Note artifacts: files created, reports generated\n"
                "- Document process: steps taken, tools used (or reasoning applied)\n"
                "- Include enough detail for synthesis to use results\n\n"
                "EXAMPLES OF LOCAL WORK WITHOUT TOOLS:\n"
                "- Analyze results from delegated work items\n"
                "- Synthesize information from multiple sources\n"
                "- Create structured summaries or reports\n"
                "- Generate recommendations based on findings\n"
                "- Identify patterns or insights from data\n"
                "- Plan next steps or create action items\n"
                "- Evaluate and compare options\n"
                "- Make decisions based on available information\n\n"
                "ERROR HANDLING:\n"
                "- Tool errors → Mark FAILED with specific error message\n"
                "- Missing data → Mark FAILED, note what's missing\n"
                "- Partial success → Decide if acceptable for DONE or needs retry\n"
                "- Blocked by dependencies → Skip (don't execute yet)\n\n"
                "IMPORTANT:\n"
                "- Only execute LOCAL items (kind=LOCAL)\n"
                "- Respect dependencies - blocked items wait for dependencies\n"
                "- Always mark status after execution attempt\n"
                "- Focus on quality - results will be synthesized later"
            ),
            max_iterations=self._iteration_limits.execution
        )
        execution_phase.add_validator(execution_validator)

        monitoring_phase = PhaseDefinition(
            name=OrchestratorPhase.MONITORING.value,
            description="Interpret responses and manage work item lifecycle",
            tools=[mark_status_tool, delegate_tool, list_nodes_tool, create_plan_tool],
            guidance=(
                "PHASE: MONITORING - Interpret responses from delegated agents and decide next steps.\n\n"
                "DECISION FRAMEWORK:\n"
                "1. REVIEW responses in 'Current Work Plan' section above to see items with responses\n"
                "2. EVALUATE each response:\n"
                "   - Is it complete and satisfactory? → Mark 'done'\n"
                "   - Does it need clarification or more detail? → Re-delegate with follow-up question\n"
                "   - Is the work truly impossible? → Mark 'failed' (with explanation)\n"
                "   - Is the response ambiguous? → Re-delegate to ask specific questions\n\n"
                "RE-DELEGATION (Preferred for Follow-ups):\n"
                "- Use DelegateTaskTool to continue conversation with the same agent\n"
                "- Thread context is preserved automatically - agent sees previous conversation\n"
                "- Examples: 'Please elaborate on X', 'Can you clarify Y?', 'Provide more detail on Z'\n"
                "- This enables iterative refinement and quality improvement\n\n"
                "MARKING STATUS (Final Decision Only):\n"
                "- Use MarkWorkItemStatusTool ONLY when you're certain:\n"
                "  * 'done': Work is complete, quality is acceptable, requirements met\n"
                "  * 'failed': Work cannot be completed, retries exhausted, or fundamentally impossible\n"
                "- Do NOT rush to mark 'done' - asking for clarification is better than accepting incomplete work\n\n"
                "IMPORTANT:\n"
                "- Thread reuse: When re-delegating, the agent automatically sees previous responses\n"
                "- Multi-turn conversations: Feel free to ask multiple follow-ups to get quality results\n"
                "- Respect retry limits: Check retry_count before marking 'failed'\n"
                "- Quality over speed: Better to re-delegate than accept poor results"
            ),
            max_iterations=self._iteration_limits.monitoring
        )
        monitoring_phase.add_validator(monitoring_validator)

        synthesis_phase = PhaseDefinition(
            name=OrchestratorPhase.SYNTHESIS.value,
            description="Summarize completed work and produce final deliverables",
            tools=domain_tools_list,  # Domain tools for synthesis
            guidance=(
                "PHASE: SYNTHESIS - Combine all completed work into cohesive final deliverable.\n\n"
                "PURPOSE:\n"
                "- Synthesize results from all DONE work items\n"
                "- Produce final deliverable that answers original request\n"
                "- Provide context, insights, and actionable conclusions\n"
                "- Create value from completed work\n\n"
                "SYNTHESIS WORKFLOW:\n"
                "1. Review 'Current Work Plan' section above to see all work items and their results\n"
                "2. For each DONE item:\n"
                "   - Extract key findings and results\n"
                "   - Identify how it contributes to overall objective\n"
                "   - Note important artifacts or outputs\n"
                "3. Combine results into coherent narrative\n"
                "4. Structure synthesis logically (see below)\n"
                "5. Address original request and objective\n\n"
                "SYNTHESIS STRUCTURE:\n"
                "- Overview: Brief summary of what was requested and accomplished\n"
                "- Key Findings: Main results from each completed work item\n"
                "  * Present findings logically (by topic, chronology, or priority)\n"
                "  * Include specific data, insights, or outputs\n"
                "- Analysis/Insights: Patterns, conclusions, or deeper understanding\n"
                "  * Connect findings across work items\n"
                "  * Highlight significant discoveries\n"
                "- Deliverables: Final outputs, artifacts, or products\n"
                "  * Reports, data files, analysis results\n"
                "  * Links, references, or resources\n"
                "- Limitations: Note any FAILED items or incomplete work (if any)\n"
                "  * Brief explanation of what couldn't be completed\n"
                "  * Impact on overall deliverable\n"
                "- Recommendations: Next steps or follow-up actions (if applicable)\n\n"
                "HANDLING FAILED ITEMS:\n"
                "- If all items DONE → Full success synthesis\n"
                "- If some items FAILED but valuable work completed:\n"
                "  * Synthesize successful items\n"
                "  * Mention failures briefly with context\n"
                "  * Note impact on completeness\n"
                "- If most/all items FAILED → Report what was attempted and why it failed\n\n"
                "HANDLING INCOMPLETE WORK (FORCED SYNTHESIS):\n"
                "- If work items are still PENDING or IN_PROGRESS:\n"
                "  * Summarize what WAS completed successfully\n"
                "  * List incomplete items and their current status\n"
                "  * Explain why work couldn't be fully completed\n"
                "  * Provide value from partial results if possible\n"
                "- Example: 'Completed 2 of 4 tasks. Found X and Y. Items Z and W are blocked by...'\n"
                "- Focus on DELIVERING VALUE from what was accomplished, not apologizing\n\n"
                "QUALITY CHECKLIST:\n"
                "✓ Does synthesis answer the original request?\n"
                "✓ Are all DONE item results included and explained?\n"
                "✓ Is narrative coherent and well-structured?\n"
                "✓ Are key insights and takeaways highlighted?\n"
                "✓ Are deliverables clearly identified?\n"
                "✓ Is synthesis concise yet comprehensive?\n\n"
                "SYNTHESIS STYLE:\n"
                "- Focus on VALUE delivered, not process details\n"
                "- Be concise but comprehensive\n"
                "- Highlight achievements and outcomes\n"
                "- Use clear, professional language\n"
                "- Structure for easy consumption\n\n"
                "IMPORTANT:\n"
                "- Focus on RESULTS, not internal process\n"
                "- Synthesize for the end user, not internal tracking\n"
                "- Quality over length - be thorough but concise\n"
                "- Combine all completed work into unified deliverable"
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
            # Print work plan after phase change
            self._print_work_plan_after_phase(final_phase)
        
        return final_phase
    
    def can_finish_now(self, current_phase: str) -> bool:
        """
        Determine if orchestrator can finish execution now.
        
        CLEAR LOGIC - Three cases:
        1. Work is complete (all DONE/FAILED) → Finish
        2. Waiting for delegated responses with no actionable work → Finish
        3. In SYNTHESIS phase (terminal) → Finish
        
        Actionable work means:
        - Local items ready to execute (has_local_ready)
        - Remote items ready to delegate (has_remote_ready)
        - Responses that need processing (has_responses)
        
        Root causes (cycles, blocked items, phase limits) are handled by
        phase transition logic, not here. This keeps finish logic simple.
        
        Args:
            current_phase: Current phase name
            
        Returns:
            True if can finish, False if more work needed
        """
        try:
            # Get work plan status
            context = self.get_phase_context()
            if not context or not context.work_plan_status:
                # No work plan - allow finish (defensive)
                return True
            
            status = context.work_plan_status
            
            # Case 1: Work complete (all items DONE or FAILED)
            if status.is_complete:
                return True
            
            # Case 2: Delegated items waiting for responses (router flow)
            # Allow finish if:
            # - We have remote items waiting (already delegated)
            # - No responses to process (has_responses=False)
            # - No local work ready to execute (has_local_ready=False)
            # - No remote work ready to delegate (has_remote_ready=False)
            #
            # This means we've delegated everything we can and are waiting
            # for the router to re-invoke us when responses arrive.
            if status.has_remote_waiting:
                if (not status.has_responses 
                    and not status.has_local_ready 
                    and not status.has_remote_ready):
                    return True
            
            # Case 3: In SYNTHESIS phase (terminal - always allow finish)
            try:
                current_phase_enum = OrchestratorPhase(current_phase)
                if current_phase_enum == OrchestratorPhase.SYNTHESIS:
                    return True
            except ValueError:
                pass  # Unknown phase, fall through
            
            # Otherwise, keep working
            return False
            
        except Exception as e:
            # On error, allow finish (defensive - don't block forever)
            return True
    
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
            
            # Cycle detection - force to SYNTHESIS
            if next_phase in visited:
                self._log_cascade(transitions + [next_phase], cascade_num, 'cycle')
                return OrchestratorPhase.SYNTHESIS.value
            
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
            print(f"🔄 Phase Cascade: {path}")
        elif reason == 'cycle':
            print(f"⚠️  Cycle Detected: {path} (forcing SYNTHESIS)")
        elif reason == 'max_transitions':
            print(f"⚠️  Max Transitions: {path}")
        elif reason == 'invalid':
            print(f"⚠️  Invalid Transition: {path}")

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
        # Handle None context gracefully
        if not context or not context.work_plan_status:
            return OrchestratorPhase.PLANNING.value  # No context or work plan, start planning

        status = context.work_plan_status
        
        # Check iteration limits first
        if self._is_phase_limit_exceeded(current_phase):
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
            # Check if work is complete
            if status.is_complete:
                return OrchestratorPhase.SYNTHESIS.value
            # If still have local ready items, stay in execution (LLM may need multiple iterations)
            elif status.has_local_ready:
                return OrchestratorPhase.EXECUTION.value
            # Otherwise move to monitoring
            else:
                return OrchestratorPhase.MONITORING.value

        elif current_phase_enum == OrchestratorPhase.MONITORING:
            # Check if work is complete
            if status.is_complete:
                return OrchestratorPhase.SYNTHESIS.value
            # PRIORITY: Stay in monitoring if we still have responses to interpret
            # (Process responses BEFORE transitioning to handle new pending work)
            elif status.has_responses:
                return OrchestratorPhase.MONITORING.value
            # Check for all-blocked scenario (no actionable work)
            # If all remaining items are blocked and we can't make progress, force SYNTHESIS
            elif (status.blocked_items > 0 and 
                  status.pending_items == 0 and 
                  not status.has_local_ready and 
                  not status.has_remote_waiting):
                print(f"⚠️  All Items Blocked ({status.blocked_items}) - Forcing SYNTHESIS")
                return OrchestratorPhase.SYNTHESIS.value
            # Go back to execution if we have local ready items
            # (Check this BEFORE pending items to prioritize actual work over allocation)
            elif status.has_local_ready:
                return OrchestratorPhase.EXECUTION.value
            # Go back to allocation if we have pending items (and no responses)
            # Note: blocked items (pending=0, blocked>0) will NOT trigger this
            elif status.pending_items > 0:
                return OrchestratorPhase.ALLOCATION.value
            else:
                # No responses, no ready work, no pending work
                # Either waiting for delegated responses or all items blocked/complete
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
        print(f"⚠️  Phase Limit Exceeded: {current_phase}")
        
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
            # Return minimal context on error
            return PhaseValidationContext(
                phase_state=phase_state,
                thread_id=self._thread_id,
                node_uid=self._node_uid
            )
    
    def _print_work_plan_after_phase(self, phase: str) -> None:
        """Print work plan status after phase transition."""
        try:
            from elements.nodes.common.workload import WorkItemStatus, WorkItemKind
            
            workspace_service = self._get_workload_service()
            plan = workspace_service.load_work_plan(self._thread_id, self._node_uid)
            
            if not plan or not plan.items:
                return
            
            status_summary = workspace_service.get_work_plan_status(self._thread_id, self._node_uid)
            
            # Compact one-line status
            status_parts = []
            if status_summary.pending_items > 0:
                status_parts.append(f"⏸️ {status_summary.pending_items} Pending")
            if status_summary.in_progress_items > 0:
                status_parts.append(f"🔄 {status_summary.in_progress_items} In Progress")
            if status_summary.done_items > 0:
                status_parts.append(f"✅ {status_summary.done_items} Done")
            if status_summary.failed_items > 0:
                status_parts.append(f"❌ {status_summary.failed_items} Failed")
            
            extras = []
            if status_summary.blocked_items > 0:
                extras.append(f"🚫 {status_summary.blocked_items} Blocked")
            if status_summary.waiting_items > 0:
                extras.append(f"⏳ {status_summary.waiting_items} Waiting")
            
            extra_str = f" [{', '.join(extras)}]" if extras else ""
            
            # Print header with one-line status
            print(f"\n{'='*80}")
            print(f"📋 WORK PLAN after {phase.upper()} ({status_summary.total_items} items)")
            print(f"={'='*80}")
            print(f"Status: {' | '.join(status_parts)}{extra_str}")
            
            # Show items compactly
            for status in [WorkItemStatus.PENDING, WorkItemStatus.IN_PROGRESS, WorkItemStatus.DONE, WorkItemStatus.FAILED]:
                items = plan.get_items_by_status(status)
                if not items:
                    continue
                
                for item in items:
                    status_icon = {
                        WorkItemStatus.PENDING: "⏸️",
                        WorkItemStatus.IN_PROGRESS: "🔄",
                        WorkItemStatus.DONE: "✅",
                        WorkItemStatus.FAILED: "❌"
                    }.get(status, "❓")
                    
                    # Compact one-line per item
                    kind = "local" if item.kind == WorkItemKind.LOCAL else f"→{item.assigned_uid}"
                    item_line = f"{status_icon} {item.title[:50]}"
                    if len(item.title) > 50:
                        item_line += "..."
                    item_line += f" ({kind})"
                    
                    # Add dependency info
                    if item.dependencies:
                        completed_deps = plan.get_completed_item_ids()
                        dep_status = []
                        for dep_id in item.dependencies:
                            dep_item = plan.items.get(dep_id)
                            if dep_item:
                                dep_title = dep_item.title[:20] + "..." if len(dep_item.title) > 20 else dep_item.title
                                if dep_id in completed_deps:
                                    dep_status.append(f"✓{dep_title}")
                                else:
                                    dep_status.append(f"✗{dep_title}")
                            else:
                                # Fallback if dependency not found
                                dep_status.append(f"?{dep_id}")
                        item_line += f" [depends on: {', '.join(dep_status)}]"
                    
                    # Show responses if present with processed status
                    if item.result_ref and item.result_ref.responses:
                        response_count = len(item.result_ref.responses)
                        processed_count = sum(1 for r in item.result_ref.responses if r.processed)
                        unprocessed_count = response_count - processed_count
                        
                        if response_count == 1:
                            # Single response - show content with status
                            latest = item.result_ref.latest_response
                            status_marker = "✓" if latest.processed else "⚡"
                            resp_preview = latest.content[:100].replace('\n', ' ')
                            item_line += f"\n      {status_marker} {resp_preview}..."
                        else:
                            # Multiple responses - show count summary first
                            item_line += f"\n      💬 {response_count} responses ({processed_count}✓ processed, {unprocessed_count}⚡ pending)"
                            # Show ALL responses with their status
                            for resp in item.result_ref.responses:
                                status_marker = "✓" if resp.processed else "⚡"
                                resp_preview = resp.content[:100].replace('\n', ' ')
                                item_line += f"\n      {status_marker} {resp_preview}..."
                    
                    print(f"   {item_line}")
            
            print(f"{'='*80}\n")
        except Exception as e:
            pass
    
    def get_dynamic_context_messages(self, phase_name: str) -> List["ChatMessage"]:
        """
        Provide fresh workspace and work plan context before each LLM call.
        
        This ensures the LLM always sees the current state of:
        - Workspace facts and results
        - Work plan with all items and their responses
        
        Called by strategy before each LLM interaction, following the same
        pattern as get_phase_validation().
        
        Args:
            phase_name: Current phase name (unused, but kept for consistency)
            
        Returns:
            List of ChatMessage with fresh context
        """
        from elements.llms.common.chat.message import ChatMessage, Role
        
        messages = []
        
        try:
            workspace_service = self._get_workload_service().get_workspace_service()
            
            # Fresh workspace context (facts, results, variables)
            workspace_summary = self._build_workspace_summary_internal(workspace_service)
            if workspace_summary:
                messages.append(ChatMessage(
                    role=Role.USER,
                    content=f"Current Context:\n{workspace_summary}"
                ))
            
            # Fresh work plan snapshot (with all responses)
            plan = workspace_service.load_work_plan(self._thread_id, self._node_uid)
            if plan:
                plan_snapshot = self._build_plan_snapshot_internal(plan, workspace_service)
                messages.append(ChatMessage(
                    role=Role.USER,
                    content=f"Current Work Plan:\n{plan_snapshot}"
                ))
        
        except Exception as e:
            # Fail gracefully - don't break execution if context building fails
            print(f"⚠️  Error building dynamic context: {e}")
        
        return messages
    
    def _build_workspace_summary_internal(self, workspace_service) -> str:
        """
        Build workspace summary (facts, results, variables).
        
        Note: Responses are no longer in facts - they're in work items.
        """
        lines = []

        # Key facts
        facts = workspace_service.get_facts(self._thread_id)
        if facts:
            lines.append(f"Facts ({len(facts)}):")
            for fact in facts[:5]:
                lines.append(f"  - {fact}")

        # Recent results
        results = workspace_service.get_results(self._thread_id)
        if results:
            lines.append(f"\nResults ({len(results)}):")
            for result in results[-3:]:
                lines.append(f"  - {result.agent_name}: {result.content[:50]}...")

        # Key variables (optional context)
        variables = workspace_service.get_all_variables(self._thread_id)
        if variables:
            # Only show non-internal variables
            public_vars = {k: v for k, v in variables.items()
                           if not k.startswith('_') and k not in ['orchestrator_uid', 'original_task_id']}
            if public_vars:
                lines.append(f"\nVariables ({len(public_vars)}):")
                for key, value in list(public_vars.items())[:3]:
                    lines.append(f"  - {key}: {str(value)[:30]}...")

        return "\n".join(lines) if lines else ""
    
    def _build_plan_snapshot_internal(self, plan, workspace_service) -> str:
        """Build comprehensive work plan snapshot with responses."""
        from elements.nodes.common.workload import WorkItemStatus
        
        status_summary = workspace_service.get_work_plan_status(self._thread_id, self._node_uid)
        
        lines = [
            f"Work Plan: {status_summary.total_items} items total",
            f"Status: pending={status_summary.pending_items}, in_progress={status_summary.in_progress_items} (waiting={status_summary.waiting_items}), done={status_summary.done_items}, failed={status_summary.failed_items}",
            f"Complete: {status_summary.is_complete}"
        ]

        if plan:
            lines.append(f"\nPlan Summary: {plan.summary}")

            # Show items by status with full details including responses
            for status in [WorkItemStatus.PENDING, WorkItemStatus.IN_PROGRESS, WorkItemStatus.DONE]:
                items = plan.get_items_by_status(status)
                if items:
                    lines.append(f"\n{status.value.upper()} ({len(items)}):")
                    for item in items[:5]:  # Show up to 5 items per status
                        status_info = f"  - {item.title} (ID: {item.id})"
                        if item.dependencies:
                            status_info += f" [depends on: {', '.join(item.dependencies)}]"
                        if item.assigned_uid:
                            status_info += f" [assigned to: {item.assigned_uid}]"
                        if item.retry_count > 0:
                            status_info += f" [retries: {item.retry_count}/{item.max_retries}]"
                        lines.append(status_info)
                        
                        # Show responses if present (for interpretation)
                        if item.result_ref and item.result_ref.has_responses:
                            response_count = item.result_ref.response_count
                            if response_count == 1:
                                # Single response - show full content
                                latest = item.result_ref.latest_response
                                lines.append(f"    Response from {latest.from_uid}:")
                                lines.append(f"      {latest.content}")
                            else:
                                # Multi-turn conversation - show all responses with sequence
                                lines.append(f"    Conversation ({response_count} responses):")
                                for resp in item.result_ref.responses:
                                    lines.append(f"      [{resp.sequence}] {resp.from_uid}: {resp.content}")
                    
                    if len(items) > 5:
                        lines.append(f"    ... and {len(items) - 5} more")

        return "\n".join(lines)
