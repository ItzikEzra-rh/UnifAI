"""
Orchestrator node implementation.

This node coordinates work execution by:
1. Creating work plans from incoming tasks
2. Delegating work items to adjacent nodes
3. Monitoring responses and updating plan status
4. Synthesizing results when complete
"""

from typing import Optional, Any, List, ClassVar, Dict
from graph.state.state_view import StateView
from elements.llms.common.chat.message import ChatMessage, Role
from elements.tools.common.base_tool import BaseTool
from elements.nodes.common.base_node import BaseNode
from elements.nodes.common.capabilities.iem_capable import IEMCapableMixin
from elements.nodes.common.capabilities.llm_capable import LlmCapableMixin
from elements.nodes.common.capabilities.agent_capable import AgentCapableMixin
from elements.nodes.common.capabilities.workload_capable import WorkloadCapableMixin
from elements.nodes.common.agent import AgentConfig
from elements.nodes.common.agent.execution import ExecutionMode
from elements.nodes.common.agent.constants import StrategyType
from elements.nodes.common.agent.delegation_policy import DelegationPolicy, PermissiveDelegationPolicy
from elements.tools.common.execution.models import ExecutorConfig
from elements.nodes.common.workload import Task, WorkItemStatus, WorkItemKind, AgentResult
from .orchestrator_phase_provider import OrchestratorPhaseProvider
from .delegation_policy import OrchestratorDelegationPolicy
from elements.tools.builtin import (
    CreateOrUpdateWorkPlanTool,
    AssignWorkItemTool,
    MarkWorkItemStatusTool,
    SummarizeWorkPlanTool,
    ListAdjacentNodesTool,
    GetNodeCardTool,
    DelegateTaskTool
)


# ExecutionPhase import removed as it's not used in this file


class OrchestratorNode(
    WorkloadCapableMixin,
    IEMCapableMixin,
    AgentCapableMixin,
    LlmCapableMixin,
    BaseNode
):
    """
    Orchestrator node that plans and delegates work.
    
    Uses PlanAndExecuteStrategy to:
    - Decompose tasks into work items
    - Delegate to adjacent nodes based on capabilities
    - Monitor execution progress
    - Handle responses and update plans
    
    Key features:
    - Re-entrant: maintains state in workspace between visits
    - Flexible: can execute local work or delegate
    - Generic: any node can use orchestration with appropriate tools
    """

    READS: ClassVar[set[str]] = set()
    WRITES: ClassVar[set[str]] = set()

    def __init__(
            self,
            *,
            llm: Any,
            tools: List[BaseTool] = None,
            system_message: str = "",
            max_rounds: int = 20,
            **kwargs: Any
    ):
        """
        Initialize orchestrator node.
        
        Args:
            llm: Language model for planning and decision making
            tools: Domain-specific tools (orchestration tools added automatically)
            system_message: Custom system message for the orchestrator
            max_rounds: Maximum planning/execution rounds
            **kwargs: Additional arguments for parent classes
        """
        # Store domain specialization separately for adjacency info
        self.domain_specialization = system_message

        super().__init__(
            llm=llm,
            system_message=self._build_complete_system_message(),
            **kwargs
        )
        self.max_rounds = max_rounds
        self.base_tools = tools or []
        self._updated_threads = set()  # Track threads updated during batch processing

    def run(self, state: StateView) -> StateView:
        """
        Main orchestrator execution.
        
        Process:
        1. Handle incoming task packets (batch processing)
        2. Update work plan based on responses
        3. Run planning/execution if needed (once per thread)
        """
        # Process all incoming packets with batching
        self.process_packets_batched(state)

        return state

    def process_packets_batched(self, state: StateView) -> None:
        """
        Process all incoming packets with intelligent batching.
        
        Benefits of batching:
        1. Ingest all responses before planning - better decision making
        2. Run orchestration cycle once per thread - reduces redundant cycles
        3. Better resource utilization and lower latency
        """
        # Clear updated threads from previous batch
        self._updated_threads.clear()

        # Process all packets first (ingest phase)
        packets = list(self.inbox_packets())

        if not packets:
            return

        for i, packet in enumerate(packets):
            try:
                self.handle_task_packet(packet)
            finally:
                self.acknowledge(packet.id)

        # Run orchestration cycles for updated threads
        for thread_id in self._updated_threads:
            status_summary = self.workspaces.get_work_plan_status(thread_id, self.uid)

            # Always run orchestration cycle - even if plan is complete
            # (Complete plans can receive new requests that add new work items)
            self._run_orchestration_cycle(thread_id, "Processing after batch")
            
            # Re-check status after orchestration
            status_summary = self.workspaces.get_work_plan_status(thread_id, self.uid)
            
            # Finalize if work is complete
            if status_summary.is_complete:
                final_result = self._get_final_orchestration_result(thread_id)
                if final_result:
                    self._finalize_completed_work(thread_id, final_result)

    def handle_task_packet(self, packet) -> None:
        """
        Handle task packet - designed for batch processing.
        
        This method is called by process_packets_batched() for each packet.
        It extracts and processes the task, updating the work plan as needed.
        Updated threads are tracked in self._updated_threads for later orchestration.
        
        Args:
            packet: Task packet to handle
        """
        task = packet.extract_task()
        task.mark_processed(self.uid)

        if task.is_response():
            # This is a response to delegated work
            thread_id = self._handle_task_response(task)
            if thread_id:
                self._updated_threads.add(thread_id)
        else:
            # This is a new work request
            self._handle_new_work(task)
            if task.thread_id:
                self._updated_threads.add(task.thread_id)

    def _handle_task_response(self, task: Task) -> Optional[str]:
        """
        Handle response from delegated work.
        
        Enhanced to handle child thread responses:
        - If response comes from child thread, updates parent thread's work plan
        - Stores response as context for LLM interpretation instead of auto-marking DONE
        - Only auto-marks for explicit success/error structures
        Returns thread_id if work plan was updated.
        """
        # Find correlation in task data
        correlation_task_id = task.correlation_task_id
        if not correlation_task_id:
            return None

        # Determine which thread to update (parent vs child thread handling)
        target_thread_id = self._resolve_target_thread_for_response(task)

        # Update work plan and workspace context
        service = self.workspaces

        # Extract response content for storage in work item
        response_content = ""
        if task.result:
            # ✅ Handle AgentResult properly (use .content field, not str())
            if isinstance(task.result, AgentResult):
                response_content = task.result.content
            else:
                response_content = str(task.result)
        elif task.error:
            response_content = f"ERROR: {task.error}"
        elif task.content:
            response_content = task.content
        else:
            response_content = "Empty response"

        # NOTE: Responses are stored in WorkItem.result_ref.responses[]
        # They will be shown in the work plan snapshot automatically
        # No need to duplicate them in facts

        success = False

        # ✅ ARCHITECTURE: LLM always interprets responses (except explicit errors)
        # The LLM will use mark_work_item_status tool to finalize status
        
        if task.error:
            # Case A: Explicit ERROR - Auto-mark FAILED (errors are unambiguous)
            success = service.ingest_task_response_for_work_item(
                thread_id=target_thread_id,
                owner_uid=self.uid,
                correlation_task_id=correlation_task_id,
                error=task.error  # Already a string
            )
        
        else:
            # Case B: ALL other responses → Store for LLM interpretation
            # LLM will decide if work is truly done based on:
            # - Quality of response
            # - Completeness
            # - Alignment with requirements
            # - Overall work plan context
            
            # Determine sender: task.created_by (now properly set in Task.respond_success/error)
            # Fallback to assigned_uid if needed (defensive programming)
            from_uid = task.created_by
            if not from_uid:
                # Defensive fallback: get assigned_uid from work item
                plan = service.load_work_plan(target_thread_id, self.uid)
                if plan:
                    for item in plan.items.values():
                        if item.correlation_task_id == correlation_task_id:
                            from_uid = item.assigned_uid or "unknown"
                            break
                if not from_uid:
                    from_uid = "unknown"
            
            success = service.store_task_response_for_work_item(
                thread_id=target_thread_id,
                owner_uid=self.uid,
                correlation_task_id=correlation_task_id,
                response_content=response_content,
                from_uid=from_uid,
                result_data=task.result  # ✅ Preserve all structured data (AgentResult, dict, or None)
            )

        # Return thread_id if we updated the work plan
        return target_thread_id if success else None

    def _resolve_target_thread_for_response(self, task: Task) -> str:
        """
        Resolve the target thread for updating work plan from a response.
        
        Enhanced to handle nested thread hierarchies by using ThreadService.
        Walks up the thread hierarchy to find where this orchestrator's work plan lives.
        
        Args:
            task: Response task (may be from deeply nested child thread)
            
        Returns:
            Thread ID where this orchestrator's work plan is stored
        """
        response_thread_id = task.thread_id
        if not response_thread_id:
            # No thread context, use current orchestrator thread
            return getattr(self, '_current_thread_id', None) or 'default'

        try:
            # Use thread service to find where THIS orchestrator's work plan is
            target_thread_id = self.threads.find_work_plan_owner(response_thread_id, self.uid)
            return target_thread_id or response_thread_id
        except Exception as e:
            return response_thread_id

    def _handle_new_work(self, task: Task) -> None:
        """
        Handle new work request.
        
        Sets up thread and workspace context. Orchestration runs in batch processing phase.
        This ensures all packets are processed before orchestration begins.
        """
        # Processing new work request

        # Ensure we have a thread
        thread_id = task.thread_id
        if not thread_id:
            thread = self.threads.create_root_thread(
                title="Orchestrated Work",
                objective=task.content[:100],
                initiator=self.uid
            )
            thread_id = thread.thread_id
            # Update task with the new thread_id
            task.thread_id = thread_id

        # Record the new task for response tracking
        self.workspaces.add_task(thread_id, task)

        # Add initial context to workspace
        self.workspaces.add_fact(thread_id, f"Initial request: {task.content}")
        self.workspaces.set_variable(thread_id, "orchestrator_uid", self.uid)
        self.workspaces.set_variable(thread_id, "original_task_id", task.task_id)

        # Copy any existing conversation to workspace
        self.copy_graphstate_messages_to_workspace(thread_id)

        # ✅ Orchestration will run in the batch processing loop (lines 137-143)
        # This ensures:
        # 1. Consistent behavior: 1 cycle per thread (new work OR responses)
        # 2. Better batching: All packets processed before orchestration
        # 3. Correct context: LLM sees all available information

    def _run_orchestration_cycle(self, thread_id: str, content: str) -> AgentResult:
        """
        Run a planning and execution cycle.
        
        Uses PlanAndExecuteStrategy with orchestration tools.
        Returns AgentResult with the orchestration outcome.
        """
        print(f"\n{'='*80}")
        print(f"🎯 ORCHESTRATOR CYCLE START - Thread: {thread_id}")
        print(f"{'='*80}")

        # Build conversation context
        messages = self._build_context_messages(thread_id, content)

        # Build domain tools only (provider will build built-ins)
        tools = list(self.base_tools)

        # Apply orchestrator's delegation policy to filter adjacent nodes
        delegation_policy = self._create_delegation_policy()
        all_adjacent = self.get_adjacent_nodes()
        delegable_adjacent = delegation_policy.filter_delegable_nodes(all_adjacent)

        # Create orchestrator phase provider with clean SOLID dependencies
        # NOTE: We pass filtered nodes - provider doesn't know about delegation policy
        phase_provider = OrchestratorPhaseProvider(
            domain_tools=tools,  # These are the domain tools this orchestrator can use
            get_adjacent_nodes=lambda: delegable_adjacent,  # Pass filtered nodes!
            send_task=self.send_task,  # Inject IEM sender for delegation tool
            node_uid=self.uid,
            thread_id=thread_id,
            get_workload_service=self.get_workload_service  # Clean dependency injection
            # Uses default PhaseIterationLimits (all phases = 10 iterations)
        )

        # Create strategy with unified provider
        strategy = self.create_strategy(
            tools=tools,
            strategy_type=StrategyType.PLAN_AND_EXECUTE.value,
            system_message=self._build_complete_system_message(),
            max_steps=self.max_rounds,
            phase_provider=phase_provider
        )

        # Configure execution
        config = AgentConfig(
            execution_mode=ExecutionMode.AUTO,
            executor_config=ExecutorConfig.create_balanced()
        )

        # Ensure all phase provider tools are available to the executor
        all_phase_tools = set()
        for phase_name in phase_provider.get_supported_phases():
            phase_tools = phase_provider.get_tools_for_phase(phase_name)
            all_phase_tools.update(phase_tools)

        # Add all phase tools to strategy's tool registry so they're available to executor
        for tool in all_phase_tools:
            strategy.all_tools[tool.name] = tool

        # Run agent
        result = self.run_agent(
            messages=messages,
            strategy=strategy,
            config=config
        )

        # Create AgentResult directly with the information we need
        agent_result = AgentResult(
            content=str(result.get("output", "")),
            agent_id=self.uid,
            agent_name=self.display_name,
            success=result.get("success", False),
            error=result.get("error"),
            reasoning=result.get("reasoning", ""),
            execution_metadata=result.get("metadata", {}),
            artifacts=result.get("artifacts", []) if isinstance(result.get("artifacts"), list) else [],
            metrics=result.get("metrics", {})
        )

        # Add agent result to workspace
        self.workspaces.add_result(thread_id, agent_result)

        # Display work plan snapshot
        self._print_work_plan_snapshot(thread_id)

        print(f"{'='*80}")
        print(f"✅ ORCHESTRATOR CYCLE END - Thread: {thread_id}")
        print(f"{'='*80}\n")

        return agent_result

    def _build_context_messages(self, thread_id: str, content: str) -> List[ChatMessage]:
        """
        Build conversation context for planning.
        
        Includes:
        - Conversation history (actual ChatMessages)
        - Adjacency summary
        - Workspace snapshot  
        - Work plan snapshot
        - Current request
        """
        messages = []

        # First: Add conversation history as actual ChatMessages
        conversation_history = self.workspaces.get_conversation_history(thread_id)
        if conversation_history:
            messages.extend(conversation_history)

        # Add adjacency summary as context
        adjacency_summary = self._build_adjacency_summary()
        if adjacency_summary:
            messages.append(ChatMessage(
                role=Role.SYSTEM,
                content=f"Adjacent Nodes Available:\n{adjacency_summary}"
            ))

        # Add workspace snapshot (facts, results - NOT conversation)
        workspace_summary = self._build_workspace_summary(thread_id)
        if workspace_summary:
            messages.append(ChatMessage(
                role=Role.USER,
                content=f"Current Context:\n{workspace_summary}"
            ))

        # Add work plan snapshot if exists
        plan_snapshot = self._build_plan_snapshot(thread_id)
        if plan_snapshot:
            messages.append(ChatMessage(
                role=Role.USER,
                content=f"Current Work Plan:\n{plan_snapshot}"
            ))

        # Add current request
        messages.append(ChatMessage(
            role=Role.USER,
            content=content
        ))

        return messages

    def _build_adjacency_summary(self) -> str:
        """
        Build a comprehensive summary of delegable adjacent nodes.
        
        Respects orchestrator's delegation policy - only shows nodes that
        can receive delegated work (excludes finalization path nodes).
        
        Provides enough detail for informed delegation decisions.
        Shows description and raw skills data without parsing.
        
        Returns:
            Formatted string with node info and skills
        """
        try:
            # Get orchestrator's delegation policy
            delegation_policy = self._create_delegation_policy()
            
            # Get all adjacent nodes and filter by policy
            all_adjacent = self.get_adjacent_nodes()
            delegable_nodes = delegation_policy.filter_delegable_nodes(all_adjacent)
            
            if not delegable_nodes:
                return "No delegable nodes available."

            lines = ["Available nodes for delegation:\n"]
            
            for uid, card in delegable_nodes.items():
                lines.append(f"## {card.name} (uid: {uid})")
                lines.append(f"   Type: {card.type_key}")
                lines.append(f"   Description: {card.description}")
                
                # Skills - Show raw data as-is
                if card.skills:
                    lines.append(f"   Skills: {card.skills}")
                
                lines.append("")  # Blank line between nodes
            
            return "\n".join(lines)
            
        except Exception as e:
            print(f"⚠️ [ORCHESTRATOR] Error building adjacency summary: {e}")
            # Fallback: show all adjacent nodes
            adjacent_nodes = self.get_adjacent_nodes()
            if not adjacent_nodes:
                return "No adjacent nodes available."
            
            lines = ["Available nodes (fallback - all adjacent):\n"]
            for uid, card in adjacent_nodes.items():
                lines.append(f"## {card.name} (uid: {uid})")
                lines.append("")
            
            return "\n".join(lines)

    def _build_workspace_summary(self, thread_id: str) -> str:
        """
        Build a summary of workspace-specific context.
        
        NOTE: Conversation history is handled separately in _build_context_messages.
        This focuses on workspace data: facts, results, variables.
        """
        lines = []

        # Key facts
        facts = self.workspaces.get_facts(thread_id)
        if facts:
            lines.append(f"Facts ({len(facts)}):")
            for fact in facts[:5]:
                lines.append(f"  - {fact}")

        # Recent results
        results = self.workspaces.get_results(thread_id)
        if results:
            lines.append(f"\nResults ({len(results)}):")
            for result in results[-3:]:
                lines.append(f"  - {result.agent_name}: {result.content[:50]}...")

        # Key variables (optional context)
        variables = self.workspaces.get_all_variables(thread_id)
        if variables:
            # Only show non-internal variables
            public_vars = {k: v for k, v in variables.items()
                           if not k.startswith('_') and k not in ['orchestrator_uid', 'original_task_id']}
            if public_vars:
                lines.append(f"\nVariables ({len(public_vars)}):")
                for key, value in list(public_vars.items())[:3]:
                    lines.append(f"  - {key}: {str(value)[:30]}...")

        return "\n".join(lines) if lines else ""

    def _build_plan_snapshot(self, thread_id: str) -> str:
        """Build a comprehensive snapshot of current work plan."""
        service = self.workspaces

        summary = service.get_work_plan_status(thread_id, self.uid)
        if not summary.exists:
            return "No work plan exists yet."

        lines = [
            f"Work Plan: {summary.total_items} items total",
            f"Status: pending={summary.pending_items}, in_progress={summary.in_progress_items} (waiting={summary.waiting_items}), done={summary.done_items}, failed={summary.failed_items}",
            f"Complete: {summary.is_complete}"
        ]

        # Load plan to get detailed item information
        plan = service.load_work_plan(thread_id, self.uid)
        if plan:
            lines.append(f"\nPlan Summary: {plan.summary}")

            # Show items by status with more detail
            for status in [WorkItemStatus.PENDING, WorkItemStatus.IN_PROGRESS,
                           WorkItemStatus.DONE]:
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

    def _get_final_orchestration_result(self, thread_id: str) -> Optional[AgentResult]:
        """
        Get the final orchestration result from the completed synthesis phase.
        
        The synthesis phase should have:
        1. Called workplan.summarize tool
        2. Returned AgentFinish with the LLM's summary
        3. Created an AgentResult with that summary as content
        
        We retrieve the most recent successful result from this orchestrator.
        """
        results = self.workspaces.get_results(thread_id)
        
        # Find the most recent result from this orchestrator
        for result in reversed(results):
            if result.agent_id == self.uid:
                return result
        
        return None

    def _finalize_completed_work(self, thread_id: str, agent_result: AgentResult) -> None:
        """
        Finalize completed orchestration work.
        
        Args:
            thread_id: Thread ID
            agent_result: Final orchestration result to route
        """
        # Check if already finalized (idempotency)
        if self.workspaces.get_variable(thread_id, f"finalized_{self.uid}", False):
            return

        # Check if response is required
        original_task = self._get_original_task(thread_id)

        if original_task and original_task.should_respond:
            self._send_response(thread_id, agent_result, original_task)
        else:
            self._route_to_finalizer(thread_id, agent_result)

        # Mark as finalized
        self.workspaces.set_variable(thread_id, f"finalized_{self.uid}", True)

    def _send_response(self, thread_id: str, agent_result: AgentResult, original_task: Task) -> None:
        """Send response using original task info."""
        response_task = Task.respond_success(
            original_task=original_task,
            result=agent_result,
            processed_by=self.uid
        )

        destination = original_task.response_to or original_task.created_by
        if destination:
            self.send_task(destination, response_task)
        else:
            self._route_to_finalizer(thread_id, agent_result)

    def _route_to_finalizer(self, thread_id: str, agent_result: AgentResult) -> None:
        """Route result to nearest finalizer node."""
        try:
            topology = getattr(self.get_context(), "topology", None)
            if not topology or not topology.has_finalizer_path():
                return

            next_hop_uid = topology.get_nearest_finalizer_node()
            if not next_hop_uid:
                return

            # Create task with agent result
            task = Task(
                content="Orchestration synthesis result",
                result=agent_result,
                should_respond=False,
                thread_id=thread_id,
                created_by=self.uid,
                processed_by=self.uid
            )

            self.send_task(next_hop_uid, task)
        except Exception as e:
            pass

    def _print_work_plan_snapshot(self, thread_id: str) -> None:
        """Print a compact snapshot of the current work plan."""
        service = self.workspaces
        plan = service.load_work_plan(thread_id, self.uid)
        
        if not plan or not plan.items:
            return
        
        status_summary = service.get_work_plan_status(thread_id, self.uid)
        
        print(f"\n{'='*80}")
        print(f"📋 WORK PLAN FINAL ({status_summary.total_items} items)")
        print(f"{'='*80}")
        
        # Compact status line
        status_parts = []
        if status_summary.pending_items > 0:
            status_parts.append(f"⏸️ {status_summary.pending_items} Pending")
        if status_summary.in_progress_items > 0:
            status_parts.append(f"🔄 {status_summary.in_progress_items} In Progress")
        if status_summary.done_items > 0:
            status_parts.append(f"✅ {status_summary.done_items} Done")
        if status_summary.failed_items > 0:
            status_parts.append(f"❌ {status_summary.failed_items} Failed")
        print(f"Status: {' | '.join(status_parts)}")
        
        if status_summary.blocked_items > 0 or status_summary.waiting_items > 0:
            extras = []
            if status_summary.blocked_items > 0:
                extras.append(f"🚫 {status_summary.blocked_items} Blocked")
            if status_summary.waiting_items > 0:
                extras.append(f"⏳ {status_summary.waiting_items} Waiting")
            print(f"        {' | '.join(extras)}")
        
        # Show ALL items compactly
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
                
                # Show response if present
                if item.result_ref and item.result_ref.has_responses:
                    latest = item.result_ref.latest_response
                    if latest:
                        resp = latest.content[:40].replace('\n', ' ')
                        item_line += f" - {resp}..."
                
                print(f"   {item_line}")
        
        print(f"{'='*80}")

    @staticmethod
    def _get_orchestrator_behavior_message() -> str:
        """Compact orchestrator behavior instructions."""
        return """You are an orchestrator agent that coordinates work execution.

Core responsibilities:
1. Create detailed work plans with dependencies
2. Delegate work to appropriate adjacent nodes
3. Monitor progress and interpret responses
4. Synthesize results when complete

Key principles:
- Break tasks into manageable work items
- Match work to node capabilities  
- Track delegated work via correlation IDs
- Interpret responses carefully before marking status
- Respect retry limits (check item retry_count vs max_retries)
- Always explain reasoning for status changes"""

    def _build_complete_system_message(self) -> str:
        """Build complete system message combining behavior + specialization."""
        behavior_msg = self._get_orchestrator_behavior_message()

        if self.domain_specialization:
            # User provided domain specialization
            return f"{behavior_msg}\n\nDomain Specialization:\n{self.domain_specialization}"
        else:
            # No specialization provided
            return behavior_msg

    def _create_delegation_policy(self) -> DelegationPolicy:
        """
        Create orchestrator's delegation policy.
        
        ORCHESTRATOR'S CHOICE: Exclude finalization path nodes from delegation.
        
        This is where the orchestrator makes the decision about which nodes
        can receive delegated work. The policy encapsulates the business rule:
        "Don't delegate to finalization path nodes because I route to them
        programmatically when work completes."
        
        Returns:
            OrchestratorDelegationPolicy or fallback to permissive policy
        """
        try:
            # Get context and topology
            context = self.get_context()
            topology = context.topology if context else None
            adjacent_nodes = self.get_adjacent_nodes()
            
            # Create orchestrator-specific policy
            return OrchestratorDelegationPolicy(
                topology=topology,
                adjacent_nodes=adjacent_nodes
            )
            
        except Exception as e:
            print(f"⚠️ [ORCHESTRATOR] Error creating delegation policy: {e}")
            print(f"⚠️ [ORCHESTRATOR] Falling back to permissive policy (all nodes delegable)")
            
            # Fallback: Allow all adjacent nodes
            return PermissiveDelegationPolicy(self.get_adjacent_nodes())

    def _get_original_task(self, thread_id: str) -> Optional[Task]:
        """
        Get the original task that started this orchestration thread.
        
        Args:
            thread_id: Thread ID to get original task for
            
        Returns:
            Original task or None if not found
        """
        try:
            # Get all tasks from workspace
            tasks = self.workspaces.get_tasks(thread_id)
            if tasks:
                # Return the first task (chronologically first)
                return tasks[0]

            # Fallback: try to get from workspace variable
            original_task_id = self.workspaces.get_variable(thread_id, "original_task_id")
            if original_task_id:
                # Would need a task registry to lookup by ID, for now return None
                pass

            return None
        except Exception as e:
            return None
