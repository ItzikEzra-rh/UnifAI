"""
Orchestrator-specific phase provider implementation.

Uses clean Pydantic models and enums to define orchestrator phases professionally.
"""

from enum import Enum
from typing import List, Callable, Any, Optional
from elements.tools.common.base_tool import BaseTool
from elements.nodes.common.agent.phases.unified_phase_provider import PhaseProvider
from elements.nodes.common.agent.phases.phase_definition import PhaseSystem, PhaseDefinition
from elements.nodes.common.agent.phases.phase_protocols import PhaseState, create_phase_state
from elements.nodes.common.agent.phases.models import PhaseValidationContext
from .phases.models import PhaseIterationLimits, PhaseIterationState
from .phases.validators import (
    AllocationValidator, PlanningValidator, ExecutionValidator,
    MonitoringValidator, SynthesisValidator
)
from .context import OrchestratorContextBuilder
from .context.models import CycleTriggerReason

# Built-in orchestration tools
from elements.tools.builtin.workplan.create_or_update import CreateOrUpdateWorkPlanTool
from elements.tools.builtin.workplan.assign_item import AssignWorkItemTool
from elements.tools.builtin.workplan.mark_status import MarkWorkItemStatusTool
from elements.tools.builtin.workplan.record_execution import RecordLocalExecutionTool
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
            context_builder: Optional[OrchestratorContextBuilder] = None,
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
            context_builder: OrchestratorContextBuilder for recording phase transitions (optional)
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
        self._context_builder = context_builder

        # Configure iteration limits using Pydantic model
        self._iteration_limits = iteration_limits or PhaseIterationLimits()

        # Track iteration state using Pydantic model
        self._iteration_state = PhaseIterationState()

        # Private: Cascade safety limit
        self._max_cascade_transitions = 10

        # Orchestrator context (set by orchestrator_node before each cycle)
        self._current_orch_context = None

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
        record_execution_tool = RecordLocalExecutionTool(
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
                "YOUR ROLE IN THIS PHASE:\n"
                "- ONLY create the work plan structure (items, dependencies, assignments)\n"
                "- DO NOT execute work or delegate tasks\n"
                "- DO NOT try to use delegation tools (not available in this phase)\n"
                "- Delegation happens automatically in ALLOCATION phase (next phase)\n\n"

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
                "   - For REMOTE items: Set assigned_uid to target agent, but DO NOT delegate yet\n"
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

                "PHASE SEPARATION (IMPORTANT):\n"
                "- PLANNING phase (you are here): Create work plan structure only\n"
                "- ALLOCATION phase (next): Delegate REMOTE items to agents\n"
                "- EXECUTION phase: Execute LOCAL items\n"
                "- MONITORING phase: Review responses and results\n"
                "- SYNTHESIS phase: Create final answer\n\n"

                "CRITICAL CONSTRAINTS:\n"
                "- DO NOT try to delegate tasks (happens in ALLOCATION phase)\n"
                "- DO NOT try to execute work (happens in EXECUTION phase)\n"
                "- ONLY use CreateOrUpdateWorkPlanTool, ListAdjacentNodesTool, GetNodeCardTool\n"
                "- Once plan is created, phase will automatically transition to ALLOCATION"
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
            tools=[record_execution_tool] + domain_tools_list,
            guidance=(
                "PHASE: EXECUTION - Execute LOCAL work items directly.\n\n"

                "🎯 WORKFLOW FOR EACH LOCAL ITEM:\n"
                "1. Identify PENDING items with kind=LOCAL\n"
                "2. Check dependencies are satisfied\n"
                "3. Execute the work:\n"
                "   - Use domain tools if appropriate for the task\n"
                "   - OR execute directly using your reasoning and knowledge\n"
                "4. Record your execution:\n"
                "   RecordLocalExecutionTool(item_id='...', outcome='...')\n"
                "   → This automatically marks the item as DONE\n\n"

                "🔧 EXECUTION APPROACHES:\n"
                "WITH TOOLS: Use domain tools for specialized tasks (search, analysis, etc.)\n"
                "WITHOUT TOOLS: Execute directly using your reasoning and knowledge\n\n"

                "📝 RECORDING OUTCOMES:\n"
                "Write naturally - describe execution as a complete narrative:\n"
                "- What approach you took and why\n"
                "- What steps or tools you used\n"
                "- What results, findings, or outputs you produced\n"
                "- Any insights or conclusions you reached\n\n"

                "⚡ ONE-STEP PROCESS:\n"
                "RecordLocalExecutionTool does it all:\n"
                "  ✓ Captures what you did\n"
                "  ✓ Automatically marks as DONE\n"
                "  ✓ Makes results available for SYNTHESIS\n\n"

                "🔗 DEPENDENCIES:\n"
                "- Only execute items whose dependencies are DONE\n"
                "- Blocked items will appear in next iteration once dependencies complete\n"
                "- You may need multiple iterations if dependencies resolve sequentially\n\n"

                "⚠️  DO NOT:\n"
                "- Mark items as IN_PROGRESS (not needed for local execution)\n"
                "- Use MarkWorkItemStatusTool (not available in this phase)\n"
                "- Attempt to execute REMOTE items (use ALLOCATION → MONITORING)\n"
            ),
            max_iterations=self._iteration_limits.execution
        )
        execution_phase.add_validator(execution_validator)

        monitoring_phase = PhaseDefinition(
            name=OrchestratorPhase.MONITORING.value,
            description="Interpret responses and execution results, manage work item lifecycle",
            tools=[mark_status_tool, delegate_tool, list_nodes_tool],
            guidance=(
                "PHASE: MONITORING - Review completed work (both remote and local) and decide next actions.\n\n"
                "YOUR ROLE:\n"
                "- Review responses from REMOTE delegated agents\n"
                "- Review execution results from LOCAL work items\n"
                "- Evaluate quality and completeness of all work\n"
                "- Decide: accept, request follow-up, or mark failed\n"
                "- YOU CANNOT EXECUTE WORK YOURSELF (no direct searches, queries, or analysis)\n\n"

                "WHAT YOU MONITOR:\n"
                "1. REMOTE items: Responses from delegated agents\n"
                "   - Check work plan for items with new responses (needs your interpretation)\n"
                "   - Agent responses appear in work item conversation history\n"
                "   - Thread context preserved across multiple follow-ups\n\n"

                "2. LOCAL items: Execution results from local work\n"
                "   - Check work plan for LOCAL items marked DONE or IN_PROGRESS\n"
                "   - Review execution notes and outcomes\n"
                "   - Validate results meet requirements\n\n"

                "DECISION FRAMEWORK FOR REMOTE ITEMS:\n"
                "For each REMOTE item with a response:\n\n"

                "1. ACCEPT if response fully satisfies requirements:\n"
                "   - Complete information provided\n"
                "   - Quality is acceptable\n"
                "   - No clarification needed\n"
                "   Action: Use MarkWorkItemStatusTool to mark item as done\n\n"

                "2. REQUEST FOLLOW-UP if response needs improvement:\n"
                "   - Response is vague or incomplete\n"
                "   - Need specific clarification or detail\n"
                "   - Agent offered additional information\n"
                "   - Quality could be better\n"
                "   Action: Use DelegateTaskTool to continue conversation with same agent\n"
                "   Note: Agent sees full conversation history automatically\n\n"

                "3. MARK FAILED if work is impossible:\n"
                "   - Agent tried multiple times without success\n"
                "   - Required resources or data don't exist\n"
                "   - Task is fundamentally not achievable\n"
                "   Action: Use MarkWorkItemStatusTool to mark item as failed\n\n"

                "DECISION FRAMEWORK FOR LOCAL ITEMS:\n"
                "For each LOCAL item that was executed:\n\n"

                "1. VERIFY execution results:\n"
                "   - Read execution notes and outcomes\n"
                "   - Confirm results meet task requirements\n"
                "   - Check for errors or incomplete work\n\n"

                "2. ACCEPT if execution successful:\n"
                "   - Results satisfy requirements\n"
                "   - Execution completed without errors\n"
                "   - Item already marked DONE by execution phase (no action needed)\n\n"

                "FOLLOW-UP BEST PRACTICES (REMOTE ITEMS):\n"
                "- Ask specific questions, not generic requests\n"
                "- Reference specific parts of the response when seeking clarity\n"
                "- Use follow-ups for iterative quality improvement\n"
                "- Same work_item_id preserves conversation thread\n"
                "- Multiple follow-ups are acceptable for quality\n"
                "- Do NOT accept incomplete responses to move faster\n"
                "- Do NOT mark failed when you just need more information\n\n"

                "CRITICAL CONSTRAINTS:\n"
                "- You are a COORDINATOR, not an EXECUTOR\n"
                "- You cannot perform searches, queries, or domain operations\n"
                "- To get more information: Re-delegate to appropriate agent\n"
                "- Do NOT execute tools meant for specialized agents\n"
                "- Do NOT mark REMOTE items as IN_PROGRESS (they are already delegated)\n"
                "- Do NOT mark LOCAL items as IN_PROGRESS (they execute in EXECUTION phase)\n\n"

                "QUALITY STANDARDS:\n"
                "- Quality over speed: Multiple follow-ups better than poor results\n"
                "- Mark done only when truly satisfied\n"
                "- Clear, actionable, complete work deserves acceptance\n"
                "- Vague, incomplete, or ambiguous work deserves follow-up or rejection"
            ),
            max_iterations=self._iteration_limits.monitoring
        )
        monitoring_phase.add_validator(monitoring_validator)

        synthesis_phase = PhaseDefinition(
            name=OrchestratorPhase.SYNTHESIS.value,
            description="Create comprehensive answer from all work items regardless of status",
            tools=[],  # NO TOOLS - synthesis only produces text responses
            guidance=(
                "PHASE: SYNTHESIS - Answer user's question using ALL available information.\n\n"
                
                "⚠️  HOW TO DELIVER YOUR ANSWER:\n"
                "Your response must be DIRECT TEXT - no tool calls, no actions.\n"
                "You are in read-only analysis mode. Just think and write your answer.\n"
                "Your text response IS the final answer delivered to the user.\n\n"
                
                "YOUR MISSION:\n"
                "Extract value from EVERY work item regardless of status.\n"
                "Provide the most complete answer possible based on what was learned.\n\n"

                "SYNTHESIS WORKFLOW:\n"
                "1. Review ENTIRE work plan - all items, all statuses\n"
                "2. Extract information from each status:\n"
                "   - DONE: Use results and findings\n"
                "   - FAILED: What was learned? Why did it fail?\n"
                "   - IN_PROGRESS: Any partial results in conversation?\n"
                "   - PENDING: Why blocked? Still relevant?\n"
                "3. Construct answer that addresses user's original question\n\n"

                "ANSWER STRUCTURE:\n"
                "1. DIRECT ANSWER: Start with answer to user's question\n"
                "   - Use all available information\n"
                "   - Be specific and actionable\n\n"

                "2. SUPPORTING DETAILS:\n"
                "   - Key findings from completed work\n"
                "   - Insights from failures (negative results are valuable)\n"
                "   - Partial information if relevant\n\n"

                "3. TRANSPARENCY:\n"
                "   - State confidence level (complete/partial/uncertain)\n"
                "   - Explain limitations or gaps if any\n"
                "   - Note what worked and what didn't\n\n"

                "HANDLING DIFFERENT SCENARIOS:\n"
                "- All DONE: Comprehensive answer with full confidence\n"
                "- Mix DONE/FAILED: Answer using successes, explain what failures revealed\n"
                "- Mostly FAILED: Extract value from failures (error messages, patterns) and use reasoning\n"
                "- Still IN_PROGRESS: Use completed and partial results, note what's pending\n\n"

                "CRITICAL PRINCIPLES:\n"
                "- ALWAYS provide an answer, even if incomplete\n"
                "- Extract value from failures (they contain information)\n"
                "- Focus on answering the question, not reporting status\n"
                "- Be honest about confidence and completeness\n"
                "- Do NOT skip failed items - they tell us something\n"
                "- Do NOT apologize - deliver value from what exists\n"
                "- NO TOOL CALLS - your text response IS the final answer"
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
            work_plan_status = workspace_service.get_work_plan_status(self._thread_id, self._node_uid)

            # No conversion needed - WorkPlanStatus is now the single source of truth
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
        Determine if orchestrator should finish THIS CYCLE now.
        
        Clean separation of concerns:
        - This method handles CYCLE finishing (waiting for external events)
        - Phase transitions handle moving between phases (EXECUTION → SYNTHESIS)
        
        Return True only when:
        1. In SYNTHESIS phase (terminal, work done)
        2. Waiting for responses with no actionable work (pause until responses arrive)
        
        Do NOT return True just because work is complete - let phase transition
        logic handle EXECUTION → SYNTHESIS. Only finish cycle when in SYNTHESIS.
        
        Args:
            current_phase: Current phase name
            
        Returns:
            True if should finish cycle, False if more work needed
        """
        try:
            # Get work plan status
            context = self.get_phase_context()
            if not context or not context.work_plan_status:
                # No work plan - allow finish (defensive)
                return True

            status = context.work_plan_status

            # Case 1: In SYNTHESIS phase (terminal - can always finish)
            try:
                current_phase_enum = OrchestratorPhase(current_phase)
                if current_phase_enum == OrchestratorPhase.SYNTHESIS:
                    return True
            except ValueError:
                pass  # Unknown phase, fall through

            # Case 2: Waiting for responses with no actionable work (router flow)
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

            # Otherwise, keep working (including transitioning to SYNTHESIS if complete)
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

            # Record phase transition in context builder if available
            if self._context_builder:
                self._context_builder.record_phase_transition(
                    from_phase=current,
                    to_phase=next_phase,
                    reason=f"Cascade transition (started from {transitions[0]})"
                )

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
            # Access orchestrator context for smart decisions
            orch_ctx = self._current_orch_context

            # 🔍 DEBUG: Print current status for diagnosis
            print(f"🔍 [PLANNING] decide_next_phase called:")
            print(f"   - Has orch_ctx: {orch_ctx is not None}")
            print(f"   - status.total_items: {status.total_items}")
            print(f"   - status.pending_items: {status.pending_items}")
            print(f"   - status.blocked_items: {status.blocked_items}")
            print(f"   - status.in_progress_items: {status.in_progress_items}")
            print(f"   - status.has_remote_ready: {status.has_remote_ready}")
            print(f"   - status.has_local_ready: {status.has_local_ready}")
            print(f"   - status.is_complete: {status.is_complete}")
            if orch_ctx:
                print(f"   - Trigger reason: {orch_ctx.trigger.reason}")

            # CASE 1: No plan exists - must stay in planning to create one
            if status.total_items == 0:
                print(f"   → Decision: STAY in PLANNING (no items)")
                return OrchestratorPhase.PLANNING.value

            # CASE 2: Plan exists - use trigger reason for smart transition
            if orch_ctx:
                trigger_reason = orch_ctx.trigger.reason
                print(f"   → Has orch_ctx, trigger_reason: {trigger_reason}")

                # CASE 2A: RESPONSE_ARRIVED - skip planning, go process responses
                if trigger_reason == CycleTriggerReason.RESPONSE_ARRIVED:
                    print(f"   → CASE 2A: RESPONSE_ARRIVED")
                    # Responses don't need new planning - just process them
                    if status.has_responses:
                        print(f"   → Decision: Go to MONITORING (has_responses)")
                        return OrchestratorPhase.MONITORING.value
                    elif status.is_complete:
                        print(f"   → Decision: Go to SYNTHESIS (is_complete)")
                        return OrchestratorPhase.SYNTHESIS.value
                    else:
                        print(f"   → Decision: Go to ALLOCATION (fallback)")
                        return OrchestratorPhase.ALLOCATION.value

                # CASE 2B: NEW_REQUEST with existing plan
                elif trigger_reason == CycleTriggerReason.NEW_REQUEST:
                    print(f"   → CASE 2B: NEW_REQUEST")
                    # Check if this is a fresh plan (nothing executed yet)
                    # Note: Don't check pending_items == total_items because blocked items
                    # are counted separately. A fresh plan with dependencies will have
                    # some items blocked, but that's still a fresh plan (no work done yet).
                    all_pending = (status.done_items == 0 and
                                   status.failed_items == 0 and
                                   status.in_progress_items == 0)
                    print(
                        f"   → Fresh plan check: {all_pending} (done={status.done_items}, failed={status.failed_items}, in_progress={status.in_progress_items})")

                    if all_pending:
                        print(f"   → Fresh plan detected")
                        # Fresh plan just created - determine next phase based on what's actionable
                        if status.has_remote_ready:
                            # Has REMOTE items ready - go delegate them
                            # (Will cascade to EXECUTION if also has_local_ready)
                            print(f"   → Decision: Go to ALLOCATION (has_remote_ready=True)")
                            return OrchestratorPhase.ALLOCATION.value
                        elif status.has_local_ready:
                            # Has LOCAL items ready but NO REMOTE ready
                            # Skip ALLOCATION, go straight to EXECUTION
                            print(f"   → Decision: Go to EXECUTION (has_local_ready=True)")
                            return OrchestratorPhase.EXECUTION.value
                        elif status.blocked_items == status.total_items:
                            # Everything is blocked by dependencies (bad plan)
                            # Force SYNTHESIS to report the issue
                            print(f"   → Decision: Go to SYNTHESIS (all blocked)")
                            return OrchestratorPhase.SYNTHESIS.value
                        else:
                            # Fallback: go to ALLOCATION
                            print(f"   → Decision: Go to ALLOCATION (fallback)")
                            return OrchestratorPhase.ALLOCATION.value

                    # Not a fresh plan - work is in progress
                    print(f"   → Not a fresh plan (work in progress)")
                    if status.is_complete:
                        # Complete plan + new request = LLM might add new work
                        # But check if new items were already added and are ready
                        print(f"   → Plan was complete, checking if new items added...")
                        if status.has_remote_ready or status.has_local_ready:
                            # New items added and ready - transition to handle them
                            if status.has_remote_ready:
                                print(f"   → Decision: Go to ALLOCATION (has_remote_ready=True)")
                                return OrchestratorPhase.ALLOCATION.value
                            else:
                                print(f"   → Decision: Go to EXECUTION (has_local_ready=True)")
                                return OrchestratorPhase.EXECUTION.value
                        else:
                            # No ready items yet - give LLM chance to plan
                            print(f"   → Decision: STAY in PLANNING (complete + new request)")
                            return OrchestratorPhase.PLANNING.value
                    elif orch_ctx.health.progress_metrics.is_stalled:
                        # Stalled work - may need replanning or pivot
                        print(f"   → Decision: STAY in PLANNING (stalled)")
                        return OrchestratorPhase.PLANNING.value
                    elif status.failed_items == status.total_items > 0:
                        # All items failed - definitely need replanning
                        print(f"   → Decision: STAY in PLANNING (all failed)")
                        return OrchestratorPhase.PLANNING.value
                    else:
                        # In-progress work with new request
                        # Check if new items are ready to execute/delegate
                        print(f"   → Checking readiness for follow-up items...")
                        if status.has_remote_ready:
                            print(f"   → Decision: Go to ALLOCATION (has_remote_ready=True)")
                            return OrchestratorPhase.ALLOCATION.value
                        elif status.has_local_ready:
                            print(f"   → Decision: Go to EXECUTION (has_local_ready=True)")
                            return OrchestratorPhase.EXECUTION.value
                        else:
                            # Nothing ready yet - stay in planning to add/update items
                            print(f"   → Decision: STAY in PLANNING (no ready items)")
                            return OrchestratorPhase.PLANNING.value

            # CASE 3: Fallback if no orchestrator context (shouldn't happen normally)
            print(f"   → CASE 3: No orch_ctx (fallback)")
            if status.total_items > 0:
                print(f"   → Decision: Go to ALLOCATION (fallback, has items)")
                return OrchestratorPhase.ALLOCATION.value
            else:
                print(f"   → Decision: STAY in PLANNING (fallback, no items)")
                return OrchestratorPhase.PLANNING.value

        elif current_phase_enum == OrchestratorPhase.ALLOCATION:
            # 🔍 DEBUG: Print current status for diagnosis
            print(f"🔍 [ALLOCATION] decide_next_phase called:")
            print(f"   - status.has_local_ready: {status.has_local_ready}")
            print(f"   - status.has_remote_ready: {status.has_remote_ready}")
            print(f"   - status.has_responses: {status.has_responses}")
            print(f"   - status.has_remote_waiting: {status.has_remote_waiting}")

            # Move to execution if we have local work ready
            if status.has_local_ready:
                print(f"   → Decision: Go to EXECUTION (has_local_ready)")
                return OrchestratorPhase.EXECUTION.value
            # Move to monitoring if we have responses to interpret
            elif status.has_responses:
                print(f"   → Decision: Go to MONITORING (has_responses)")
                return OrchestratorPhase.MONITORING.value
            # If just waiting (no responses yet), stay in allocation (will finish and wait for graph)
            elif status.has_remote_waiting:
                print(f"   → Decision: STAY in ALLOCATION (has_remote_waiting, will finish)")
                return OrchestratorPhase.ALLOCATION.value  # Stay → finish
            else:
                print(f"   → Decision: STAY in ALLOCATION (default)")
                return OrchestratorPhase.ALLOCATION.value  # Stay in allocation

        elif current_phase_enum == OrchestratorPhase.EXECUTION:
            # 🔍 DEBUG: Print current status for diagnosis
            print(f"🔍 [EXECUTION] decide_next_phase called:")
            print(f"   - status.is_complete: {status.is_complete}")
            print(f"   - status.has_local_ready: {status.has_local_ready}")

            # Check if work is complete
            if status.is_complete:
                print(f"   → Decision: Go to SYNTHESIS (is_complete)")
                return OrchestratorPhase.SYNTHESIS.value
            # If still have local ready items, stay in execution (LLM may need multiple iterations)
            elif status.has_local_ready:
                print(f"   → Decision: STAY in EXECUTION (has_local_ready)")
                return OrchestratorPhase.EXECUTION.value
            # Otherwise move to monitoring
            else:
                print(f"   → Decision: Go to MONITORING (no local ready)")
                return OrchestratorPhase.MONITORING.value

        elif current_phase_enum == OrchestratorPhase.MONITORING:
            # 🔍 DEBUG: Print current status for diagnosis
            print(f"🔍 [MONITORING] decide_next_phase called:")
            print(f"   - status.total_items: {status.total_items}")
            print(f"   - status.pending_items: {status.pending_items}")
            print(f"   - status.in_progress_items: {status.in_progress_items}")
            print(f"   - status.waiting_items: {status.waiting_items}")
            print(f"   - status.done_items: {status.done_items}")
            print(f"   - status.failed_items: {status.failed_items}")
            print(f"   - status.blocked_items: {status.blocked_items}")
            print(f"   - status.has_responses: {status.has_responses}")
            print(f"   - status.has_local_ready: {status.has_local_ready}")
            print(f"   - status.has_remote_ready: {status.has_remote_ready}")
            print(f"   - status.has_remote_waiting: {status.has_remote_waiting}")
            print(f"   - status.is_complete: {status.is_complete}")

            # Check if work is complete
            if status.is_complete:
                print(f"   → Decision: Go to SYNTHESIS (is_complete)")
                return OrchestratorPhase.SYNTHESIS.value
            # PRIORITY: Stay in monitoring if we still have responses to interpret
            # (Process responses BEFORE transitioning to handle new pending work)
            elif status.has_responses:
                print(f"   → Decision: STAY in MONITORING (has_responses=True)")
                return OrchestratorPhase.MONITORING.value
            # Check for all-blocked scenario (no actionable work)
            # If all remaining items are blocked and we can't make progress, force SYNTHESIS
            elif (status.blocked_items > 0 and
                  status.pending_items == 0 and
                  not status.has_local_ready and
                  not status.has_remote_waiting):
                print(f"⚠️  All Items Blocked ({status.blocked_items}) - Forcing SYNTHESIS")
                print(f"   → Decision: Go to SYNTHESIS (all blocked)")
                return OrchestratorPhase.SYNTHESIS.value
            # Go back to execution if we have local ready items
            # (Check this BEFORE pending items to prioritize actual work over allocation)
            elif status.has_local_ready:
                print(f"   → Decision: Go to EXECUTION (has_local_ready=True)")
                return OrchestratorPhase.EXECUTION.value
            # Go back to allocation if we have pending items (and no responses)
            # Note: blocked items (pending=0, blocked>0) will NOT trigger this
            elif status.pending_items > 0:
                print(f"   → Decision: Go to ALLOCATION (pending_items={status.pending_items})")
                return OrchestratorPhase.ALLOCATION.value
            else:
                # No responses, no ready work, no pending work
                # Either waiting for delegated responses or all items blocked/complete
                print(f"   → Decision: STAY in MONITORING (waiting for responses or no actionable work)")
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

            status = workspace_service.get_work_plan_status(self._thread_id, self._node_uid)

            # Compact one-line status
            status_parts = []
            if status.pending_items > 0:
                status_parts.append(f"⏸️ {status.pending_items} Pending")
            if status.in_progress_items > 0:
                status_parts.append(f"🔄 {status.in_progress_items} In Progress")
            if status.done_items > 0:
                status_parts.append(f"✅ {status.done_items} Done")
            if status.failed_items > 0:
                status_parts.append(f"❌ {status.failed_items} Failed")

            extras = []
            if status.blocked_items > 0:
                extras.append(f"🚫 {status.blocked_items} Blocked")
            if status.waiting_items > 0:
                extras.append(f"⏳ {status.waiting_items} Waiting")

            extra_str = f" [{', '.join(extras)}]" if extras else ""

            # Print header with one-line status
            print(f"\n{'=' * 80}")
            print(f"📋 WORK PLAN after {phase.upper()} ({status.total_items} items)")
            print(f"={'=' * 80}")
            print(f"Status: {' | '.join(status_parts)}{extra_str}")

            # Show items compactly
            for item_status in [WorkItemStatus.PENDING, WorkItemStatus.IN_PROGRESS, WorkItemStatus.DONE,
                                WorkItemStatus.FAILED]:
                items = plan.get_items_by_status(item_status)
                if not items:
                    continue

                for item in items:
                    status_icon = {
                        WorkItemStatus.PENDING: "⏸️",
                        WorkItemStatus.IN_PROGRESS: "🔄",
                        WorkItemStatus.DONE: "✅",
                        WorkItemStatus.FAILED: "❌"
                    }.get(item_status, "❓")

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

                    # Show delegation conversation if present
                    if item.result and item.result.delegations:
                        delegation_count = len(item.result.delegations)
                        processed_count = sum(1 for d in item.result.delegations if d.processed)
                        pending_count = sum(1 for d in item.result.delegations if d.is_pending)
                        unprocessed_count = sum(1 for d in item.result.delegations if d.needs_attention)

                        if delegation_count == 1:
                            # Single delegation - show content with status
                            latest = item.result.delegations[0]
                            if latest.is_pending:
                                item_line += f"\n      ⏳ Waiting for response from {latest.delegated_to}"
                            elif latest.needs_attention:
                                resp_preview = latest.response_content[:100].replace('\n',
                                                                                     ' ') if latest.response_content else "No content"
                                item_line += f"\n      ⚡ NEW: {resp_preview}..."
                            else:
                                resp_preview = latest.response_content[:100].replace('\n',
                                                                                     ' ') if latest.response_content else "No content"
                                item_line += f"\n      ✓ Processed: {resp_preview}..."
                        else:
                            # Multiple delegations - show count summary
                            item_line += f"\n      💬 {delegation_count} turns ({processed_count}✓ processed, {unprocessed_count}⚡ pending, {pending_count}⏳ waiting)"
                            # Show latest exchange
                            latest = item.result.delegations[-1]
                            if latest.is_pending:
                                item_line += f"\n      ⏳ Latest: Waiting for {latest.delegated_to}"
                            elif latest.needs_attention:
                                resp_preview = latest.response_content[:100].replace('\n',
                                                                                     ' ') if latest.response_content else "No content"
                                item_line += f"\n      ⚡ Latest: {resp_preview}..."
                            else:
                                resp_preview = latest.response_content[:100].replace('\n',
                                                                                     ' ') if latest.response_content else "No content"
                                item_line += f"\n      ✓ Latest: {resp_preview}..."

                    print(f"   {item_line}")

            print(f"{'=' * 80}\n")
        except Exception as e:
            pass

    def get_dynamic_context_messages(self, phase_name: str) -> List["ChatMessage"]:
        """
        Provide fresh orchestrator context and work plan before each LLM call.
        
        This ensures the LLM always sees the current state:
        - Why this cycle is running (trigger)
        - User intent classification
        - Work plan health and progress
        - Phase history
        - Complete work plan with all items and responses
        
        All combined into ONE coherent message for better context.
        
        Called by strategy before each LLM interaction.
        
        Args:
            phase_name: Current phase name (unused, but kept for consistency)
            
        Returns:
            List of ChatMessage with fresh context (single combined message)
        """
        from elements.llms.common.chat.message import ChatMessage, Role

        messages = []

        try:
            workspace_service = self._get_workload_service().get_workspace_service()
            plan = workspace_service.load_work_plan(self._thread_id, self._node_uid)

            # Build work plan snapshot (full version for LLM)
            plan_snapshot = ""
            if plan:
                plan_snapshot = self._build_plan_snapshot_internal(plan, workspace_service, truncate_for_console=False)
            else:
                plan_snapshot = "No work plan exists yet."

            # If we have orchestrator context, format it with work plan in ONE message
            if self._current_orch_context:
                combined_context = self._current_orch_context.format_context(plan_snapshot)

                # Build truncated version for console printing
                plan_snapshot_console = ""
                if plan:
                    plan_snapshot_console = self._build_plan_snapshot_internal(plan, workspace_service, truncate_for_console=True)
                else:
                    plan_snapshot_console = "No work plan exists yet."
                combined_context_console = self._current_orch_context.format_context(plan_snapshot_console)

                # Print truncated context for debugging
                print(f"\n{'=' * 80}")
                print(f"📤 DYNAMIC CONTEXT PROVIDED TO LLM - Phase: {phase_name.upper()}")
                print(f"{'=' * 80}")
                print(combined_context_console)
                print(f"{'=' * 80}\n")

                # Send FULL context to LLM
                messages.append(ChatMessage(
                    role=Role.USER,
                    content=combined_context
                ))
            else:
                # Fallback: just show work plan (backward compatibility)
                fallback_context = f"Current Work Plan:\n{plan_snapshot}"

                # Build truncated version for console
                plan_snapshot_console = ""
                if plan:
                    plan_snapshot_console = self._build_plan_snapshot_internal(plan, workspace_service, truncate_for_console=True)
                else:
                    plan_snapshot_console = "No work plan exists yet."
                fallback_context_console = f"Current Work Plan:\n{plan_snapshot_console}"

                # Print truncated fallback context for debugging
                print(f"\n{'=' * 80}")
                print(f"📤 DYNAMIC CONTEXT PROVIDED TO LLM - Phase: {phase_name.upper()} (FALLBACK)")
                print(f"{'=' * 80}")
                print(fallback_context_console)
                print(f"{'=' * 80}\n")

                # Send FULL context to LLM
                messages.append(ChatMessage(
                    role=Role.USER,
                    content=fallback_context
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

    def _build_plan_snapshot_internal(self, plan, workspace_service, truncate_for_console: bool = False) -> str:
        """Build comprehensive work plan snapshot with responses."""
        from elements.nodes.common.workload import WorkItemStatus, WorkItemKind

        status = workspace_service.get_work_plan_status(self._thread_id, self._node_uid)

        lines = [
            f"Work Plan: {status.total_items} items total",
            f"Status: pending={status.pending_items}, in_progress={status.in_progress_items} (waiting={status.waiting_items}), done={status.done_items}, failed={status.failed_items}",
            f"Complete: {status.is_complete}"
        ]

        if plan:
            lines.append(f"\nPlan Summary: {plan.summary}")

            # Show ALL items by status - LLM needs full context
            for status in [WorkItemStatus.PENDING, WorkItemStatus.IN_PROGRESS, WorkItemStatus.DONE]:
                items = plan.get_items_by_status(status)
                if items:
                    lines.append(f"\n{status.value.upper()} ({len(items)}):")
                    for item in items:  # Show all items
                        status_info = f"  - {item.title} (ID: {item.id})"

                        # Show dependencies first (important for understanding blockers)
                        if item.dependencies:
                            status_info += f"\n    Dependencies: {item.dependencies}"

                        # Show assignment type
                        if item.kind == WorkItemKind.REMOTE:
                            status_info += f" → {item.assigned_uid}"
                        else:
                            status_info += " [LOCAL]"

                        if item.retry_count > 0:
                            status_info += f" [retries: {item.retry_count}/{item.max_retries}]"

                        lines.append(status_info)

                        # Show conversation for REMOTE items with delegation history
                        if item.result and item.result.delegations:
                            conv_summary = item.result.conversation_summary(truncate=truncate_for_console, max_chars=250)
                            for line in conv_summary.split('\n'):
                                lines.append(f"    {line}")

                        # Show local execution for LOCAL items
                        elif item.result and item.result.local_execution:
                            exec_info = item.result.local_execution
                            if exec_info.outcome:
                                outcome_text = exec_info.outcome
                                # Truncate for console readability
                                if truncate_for_console:
                                    # Handle multi-line outcomes by truncating and showing first portion
                                    outcome_lines = outcome_text.split('\n')
                                    if len(outcome_text) > 250:
                                        # Show first 250 chars across lines
                                        char_count = 0
                                        truncated_lines = []
                                        for oline in outcome_lines:
                                            if char_count + len(oline) > 250:
                                                remaining = 250 - char_count
                                                if remaining > 0:
                                                    truncated_lines.append(oline[:remaining] + "...")
                                                break
                                            truncated_lines.append(oline)
                                            char_count += len(oline)
                                        outcome_text = ' '.join(truncated_lines)  # Join with space for console
                                    else:
                                        # If short, still flatten to single line for console
                                        outcome_text = ' '.join(outcome_lines)
                                
                                lines.append(f"    Execution: {outcome_text}")

        return "\n".join(lines)
