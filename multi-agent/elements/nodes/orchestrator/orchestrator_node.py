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
from elements.tools.common.execution.models import ExecutorConfig
from elements.nodes.common.workload import Task, WorkPlanService, WorkItemStatus, WorkItemKind
from elements.tools.builtin import (
    CreateOrUpdateWorkPlanTool,
    AssignWorkItemTool,
    MarkWorkItemStatusTool,
    IngestWorkspaceResultsTool,
    IsWorkPlanCompleteTool,
    SummarizeWorkPlanTool,
    ListAdjacentNodesTool,
    GetNodeCardTool,
    DelegateTaskTool
)
from elements.nodes.common.agent.phase_tools import create_orchestrator_categorizer
from elements.nodes.common.agent.phase_protocols import (
    PhaseContextProvider, PhaseState, WorkPlanStatus, create_work_plan_status, create_phase_state,
    PhaseTransitionPolicy
)
from elements.nodes.common.agent.constants import ExecutionPhase
from elements.nodes.common.agent.primitives import AgentObservation


class OrchestratorPhaseContextProvider(PhaseContextProvider):
    """
    Concrete implementation of PhaseContextProvider for orchestrator nodes.
    
    This class encapsulates the logic for providing phase context to strategies,
    keeping the strategy decoupled from service implementations.
    """

    def __init__(self, node: 'OrchestratorNode', thread_id: str):
        """
        Initialize context provider.
        
        Args:
            node: The orchestrator node instance
            thread_id: Current thread ID
        """
        self.node = node
        self.thread_id = thread_id

    def get_phase_context(self) -> PhaseState:
        """
        Get current phase context for the orchestrator.
        
        Returns:
            PhaseState with current work plan status and context
        """
        try:
            workspace = self.node.get_workspace(self.thread_id)
            service = WorkPlanService(workspace)

            # Get status summary from service (now returns typed model)
            status_summary = service.get_status_summary(self.node.uid)

            if not status_summary.exists:
                # No plan exists
                work_plan_status = create_work_plan_status()
            else:
                # Convert typed service response to WorkPlanStatus
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
                thread_id=self.thread_id,
                node_uid=self.node.uid
            )

        except Exception as e:
            print(f"Error getting phase context: {e}")
            # Return empty state on error
            return create_phase_state(
                work_plan_status=create_work_plan_status(),
                thread_id=self.thread_id,
                node_uid=self.node.uid
            )


class OrchestratorPhaseTransitionPolicy(PhaseTransitionPolicy):
    """
    Orchestrator-specific phase transition policy.
    
    Implements orchestrator-specific logic for determining phase transitions
    based on work plan status and recent observations.
    """

    def decide(
            self,
            *,
            state: PhaseState,
            current: ExecutionPhase,
            observations: List['AgentObservation']
    ) -> ExecutionPhase:
        """
        Decide the next execution phase for orchestrator.
        
        Args:
            state: Current phase state with work plan status
            current: Current execution phase
            observations: Recent agent observations
            
        Returns:
            The next execution phase to transition to
        """
        work_plan_status = state.work_plan_status

        if not work_plan_status or work_plan_status.total_items == 0:
            return ExecutionPhase.PLANNING

        if work_plan_status.is_complete:
            return ExecutionPhase.SYNTHESIS

        if work_plan_status.pending_items > 0:
            return ExecutionPhase.ALLOCATION

        if work_plan_status.has_local_ready:
            return ExecutionPhase.EXECUTION

        if (work_plan_status.in_progress_items > 0 or
                work_plan_status.waiting_items > 0 or
                work_plan_status.has_remote_waiting):
            return ExecutionPhase.MONITORING

        # Default to monitoring if unclear
        return ExecutionPhase.MONITORING


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
        print(f"\n🚀 [DEBUG] OrchestratorNode.run() - Starting execution for {self.uid}")
        
        # Process all incoming packets with batching
        self.process_packets_batched(state)
        
        print(f"✅ [DEBUG] OrchestratorNode.run() - Completed execution for {self.uid}")
        return state

    def process_packets_batched(self, state: StateView) -> None:
        """
        Process all incoming packets with intelligent batching.
        
        Benefits of batching:
        1. Ingest all responses before planning - better decision making
        2. Run orchestration cycle once per thread - reduces redundant cycles
        3. Better resource utilization and lower latency
        """
        print(f"📦 [DEBUG] process_packets_batched() - Starting batch processing")
        
        # Clear updated threads from previous batch
        self._updated_threads.clear()

        # Process all packets first (ingest phase)
        packets = list(self.inbox_packets())
        print(f"📥 [DEBUG] Found {len(packets)} packets to process")
        
        for i, packet in enumerate(packets):
            print(f"📨 [DEBUG] Processing packet {i+1}/{len(packets)}: {packet.id}")
            try:
                self.handle_task_packet(packet)
            finally:
                self.acknowledge(packet.id)
                print(f"✅ [DEBUG] Acknowledged packet {packet.id}")

        print(f"🔄 [DEBUG] Updated threads: {self._updated_threads}")
        
        # Run orchestration cycles for updated threads (planning phase)
        for thread_id in self._updated_threads:
            print(f"🧠 [DEBUG] Checking orchestration cycle for thread {thread_id}")
            workspace = self.get_workspace(thread_id)
            service = WorkPlanService(workspace)

            status_summary = service.get_status_summary(self.uid)
            print(f"📊 [DEBUG] Thread {thread_id} status: complete={status_summary.is_complete}, total={status_summary.total_items}")
            
            if not status_summary.is_complete:
                print(f"🎯 [DEBUG] Running orchestration cycle for thread {thread_id}")
                self._run_orchestration_cycle(thread_id, "Continuing after batch response processing")
            else:
                print(f"🎉 [DEBUG] Work plan complete for thread {thread_id}")

    def handle_task_packet(self, packet) -> None:
        """
        Handle task packet - designed for batch processing.
        
        This method is called by process_packets_batched() for each packet.
        It extracts and processes the task, updating the work plan as needed.
        Updated threads are tracked in self._updated_threads for later orchestration.
        
        Args:
            packet: Task packet to handle
        """
        print(f"🔍 [DEBUG] handle_task_packet() - Extracting task from packet {packet.id}")
        task = packet.extract_task()
        task.mark_processed(self.uid)
        
        print(f"📋 [DEBUG] Task details: content='{task.content[:50]}...', is_response={task.is_response()}, thread_id={task.thread_id}")

        if task.is_response():
            # This is a response to delegated work
            print(f"📤 [DEBUG] Processing response task with correlation_id={task.correlation_task_id}")
            thread_id = self._handle_task_response(task)
            if thread_id:
                print(f"🔄 [DEBUG] Added thread {thread_id} to updated threads")
                self._updated_threads.add(thread_id)
        else:
            # This is a new work request
            print(f"📥 [DEBUG] Processing new work request")
            self._handle_new_work(task)
            if task.thread_id:
                print(f"🔄 [DEBUG] Added thread {task.thread_id} to updated threads")
                self._updated_threads.add(task.thread_id)


    def _handle_task_response(self, task: Task) -> Optional[str]:
        """
        Handle response from delegated work.
        
        Updates the work plan item status based on the response.
        Returns thread_id if work plan was updated.
        """
        print(f"🔄 [DEBUG] _handle_task_response() - Processing response from {task.created_by}")
        
        # Find correlation in task data
        correlation_task_id = task.correlation_task_id
        if not correlation_task_id:
            print(f"❌ [DEBUG] Received response without correlation ID from {task.created_by}")
            return None

        print(f"🔗 [DEBUG] Found correlation_task_id: {correlation_task_id}")

        # Update work plan
        workspace = self.get_workspace(task.thread_id)
        service = WorkPlanService(workspace)

        success = False
        if task.result:
            # Success response
            print(f"✅ [DEBUG] Processing SUCCESS response with result: {str(task.result)[:100]}...")
            success = service.ingest_task_response(
                owner_uid=self.uid,
                correlation_task_id=correlation_task_id,
                result=task.result
            )
            if success:
                print(f"✅ [DEBUG] Marked item as DONE for task {correlation_task_id}")
        elif task.error:
            # Error response
            print(f"❌ [DEBUG] Processing ERROR response: {str(task.error)[:100]}...")
            success = service.ingest_task_response(
                owner_uid=self.uid,
                correlation_task_id=correlation_task_id,
                error=str(task.error)
            )
            if success:
                print(f"❌ [DEBUG] Marked item as FAILED for task {correlation_task_id}")
        else:
            print(f"⚠️ [DEBUG] Response has neither result nor error - ignoring")

        # Return thread_id if we updated the work plan
        result_thread = task.thread_id if success else None
        print(f"🔄 [DEBUG] _handle_task_response() returning thread_id: {result_thread}")
        return result_thread


    def _handle_new_work(self, task: Task) -> None:
        """
        Handle new work request.
        
        Creates context and runs orchestration cycle.
        """
        print(f"🆕 [DEBUG] _handle_new_work() - Processing new work request")
        print(f"📝 [DEBUG] Task content: {task.content[:100]}...")
        
        # Ensure we have a thread
        thread_id = task.thread_id
        if not thread_id:
            print(f"🧵 [DEBUG] No thread_id provided, creating new thread")
            thread = self.create_thread(
                title="Orchestrated Work",
                objective=task.content[:100]
            )
            thread_id = thread.thread_id
            print(f"🧵 [DEBUG] Created new thread: {thread_id}")
        else:
            print(f"🧵 [DEBUG] Using existing thread: {thread_id}")

        # Add initial context to workspace
        print(f"💾 [DEBUG] Adding context to workspace for thread {thread_id}")
        self.add_fact_to_workspace(thread_id, f"Initial request: {task.content}")
        self.set_workspace_variable(thread_id, "orchestrator_uid", self.uid)
        self.set_workspace_variable(thread_id, "original_task_id", task.task_id)

        # Copy any existing conversation to workspace
        self.copy_graphstate_messages_to_workspace(thread_id)

        # Run orchestration
        print(f"🎯 [DEBUG] Starting orchestration cycle for thread {thread_id}")
        self._run_orchestration_cycle(thread_id, task.content)

    def _run_orchestration_cycle(self, thread_id: str, content: str) -> None:
        """
        Run a planning and execution cycle.
        
        Uses PlanAndExecuteStrategy with orchestration tools.
        """
        print(f"🔄 [DEBUG] _run_orchestration_cycle() - Starting cycle for thread {thread_id}")
        
        # Build conversation context
        print(f"💬 [DEBUG] Building context messages")
        messages = self._build_context_messages(thread_id, content)
        print(f"💬 [DEBUG] Built {len(messages)} context messages")

        # Build tools (domain + orchestration)
        print(f"🔧 [DEBUG] Building orchestration tools")
        tools = self._build_orchestration_tools(thread_id)
        print(f"🔧 [DEBUG] Built {len(tools)} tools: {[tool.name for tool in tools]}")

        # Create tool categorizer
        print(f"📂 [DEBUG] Creating tool categorizer")
        tool_categorizer = create_orchestrator_categorizer(tools)

        # Create phase context provider
        print(f"📊 [DEBUG] Creating phase context provider")
        context_provider = OrchestratorPhaseContextProvider(self, thread_id)

        # Create phase transition policy
        print(f"🔀 [DEBUG] Creating phase transition policy")
        transition_policy = OrchestratorPhaseTransitionPolicy()

        # Create strategy with typed providers
        print(f"🧠 [DEBUG] Creating PlanAndExecute strategy")
        strategy = self.create_strategy(
            tools=tools,
            strategy_type=StrategyType.PLAN_AND_EXECUTE.value,
            system_message=self._build_complete_system_message(),
            max_steps=self.max_rounds,
            phase_tool_provider=tool_categorizer,
            phase_context_provider=context_provider,
            phase_transition_policy=transition_policy
        )
        print(f"🧠 [DEBUG] Strategy created successfully")

        # Configure execution
        print(f"⚙️ [DEBUG] Configuring agent execution")
        config = AgentConfig(
            execution_mode=ExecutionMode.AUTO,
            executor_config=ExecutorConfig.create_balanced()
        )

        # Run agent
        print(f"🚀 [DEBUG] Starting agent execution")
        result = self.run_agent(
            messages=messages,
            strategy=strategy,
            config=config
        )

        if result.get("success"):
            print(f"✅ [DEBUG] Orchestration cycle COMPLETED successfully")
        else:
            print(f"❌ [DEBUG] Orchestration FAILED: {result.get('error')}")
            
        print(f"🔄 [DEBUG] _run_orchestration_cycle() - Finished cycle for thread {thread_id}")

    def _build_context_messages(self, thread_id: str, content: str) -> List[ChatMessage]:
        """
        Build conversation context for planning.
        
        Includes:
        - Adjacency summary
        - Workspace snapshot
        - Current request
        """
        messages = []

        # Add adjacency summary as context
        adjacency_summary = self._build_adjacency_summary()
        if adjacency_summary:
            messages.append(ChatMessage(
                role=Role.SYSTEM,
                content=f"Adjacent Nodes Available:\n{adjacency_summary}"
            ))

        # Add workspace snapshot
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

    def _build_orchestration_tools(self, thread_id: str) -> List[BaseTool]:
        """
        Build complete tool set for orchestration.
        
        Single Responsibility: Coordinates tool building by delegating
        to specialized methods for each tool category.
        """
        tools = list(self.base_tools)  # Copy base tools

        # Build accessor functions for dependency injection
        accessors = self._build_tool_accessors(thread_id)

        # Add each category of tools
        tools.extend(self._build_workplan_tools(accessors))
        tools.extend(self._build_topology_tools(accessors))
        tools.extend(self._build_delegation_tools(accessors))

        return tools

    def _build_tool_accessors(self, thread_id: str) -> Dict[str, Any]:
        """
        Build accessor functions for tool dependency injection.
        
        Single Responsibility: Creates all accessor closures in one place.
        """
        return {
            'get_workspace': lambda: self.get_workspace(thread_id),
            'get_thread_id': lambda: thread_id,
            'get_owner_uid': lambda: self.uid,
            'get_adjacent_nodes': lambda: self.get_adjacent_nodes()
        }

    def _build_workplan_tools(self, accessors: Dict[str, Any]) -> List[BaseTool]:
        """Build WorkPlan management tools."""
        return [
            CreateOrUpdateWorkPlanTool(
                accessors['get_workspace'],
                accessors['get_thread_id'],
                accessors['get_owner_uid']
            ),
            AssignWorkItemTool(accessors['get_workspace'], accessors['get_owner_uid']),
            MarkWorkItemStatusTool(accessors['get_workspace'], accessors['get_owner_uid']),
            IngestWorkspaceResultsTool(accessors['get_workspace'], accessors['get_owner_uid']),
            IsWorkPlanCompleteTool(accessors['get_workspace'], accessors['get_owner_uid']),
            SummarizeWorkPlanTool(accessors['get_workspace'], accessors['get_owner_uid'])
        ]

    def _build_topology_tools(self, accessors: Dict[str, Any]) -> List[BaseTool]:
        """Build topology introspection tools."""
        return [
            ListAdjacentNodesTool(accessors['get_adjacent_nodes']),
            GetNodeCardTool(accessors['get_adjacent_nodes'])
        ]

    def _build_delegation_tools(self, accessors: Dict[str, Any]) -> List[BaseTool]:
        """Build task delegation tools."""

        def check_adjacency(uid: str) -> bool:
            return uid in accessors['get_adjacent_nodes']()

        return [
            DelegateTaskTool(
                send_task=self.send_task,
                get_owner_uid=accessors['get_owner_uid'],
                get_workspace=accessors['get_workspace'],
                check_adjacency=check_adjacency
            )
        ]


    def _build_adjacency_summary(self) -> str:
        """Build a compact summary of adjacent nodes."""
        adjacent_nodes = self.get_adjacent_nodes()
        if not adjacent_nodes:
            return "No adjacent nodes available."

        lines = []
        for uid, card in adjacent_nodes.items():
            # Extract key capabilities
            caps = list(card.capabilities)[:3] if card.capabilities else []
            cap_str = ", ".join(caps) if caps else "general"

            # Count skills
            tool_count = len(card.skills.get('tools', []))
            retriever_count = len(card.skills.get('retrievers', []))

            lines.append(
                f"- {card.name} (uid: {uid}): {card.description[:50]}... "
                f"[{cap_str}] Tools: {tool_count}, Retrievers: {retriever_count}"
            )

        return "\n".join(lines)

    def _build_workspace_summary(self, thread_id: str) -> str:
        """Build a summary of workspace context."""
        workspace = self.get_workspace(thread_id)
        context = workspace.context

        lines = []

        # Key facts
        if context.facts:
            lines.append(f"Facts ({len(context.facts)}):")
            for fact in context.facts[:5]:
                lines.append(f"  - {fact}")

        # Recent results
        if context.results:
            lines.append(f"\nResults ({len(context.results)}):")
            for result in context.results[-3:]:
                lines.append(f"  - {result.agent_name}: {result.content[:50]}...")

        return "\n".join(lines) if lines else ""

    def _build_plan_snapshot(self, thread_id: str) -> str:
        """Build a comprehensive snapshot of current work plan."""
        workspace = self.get_workspace(thread_id)
        service = WorkPlanService(workspace)

        summary = service.get_status_summary(self.uid)
        if not summary.exists:
            return "No work plan exists yet."

        lines = [
            f"Work Plan: {summary.total_items} items total",
            f"Status: pending={summary.pending_items}, waiting={summary.waiting_items}, done={summary.done_items}, failed={summary.failed_items}",
            f"Complete: {summary.is_complete}"
        ]

        # Load plan to get detailed item information
        plan = service.load(self.uid)
        if plan:
            lines.append(f"\nPlan Summary: {plan.summary}")
            
            # Show items by status with more detail
            for status in [WorkItemStatus.PENDING, WorkItemStatus.WAITING, WorkItemStatus.IN_PROGRESS, WorkItemStatus.DONE]:
                items = plan.get_items_by_status(status)
                if items:
                    lines.append(f"\n{status.value.upper()} ({len(items)}):")
                    for item in items[:5]:  # Show up to 5 items per status
                        status_info = f"  - {item.title} (ID: {item.id})"
                        if item.dependencies:
                            status_info += f" [depends on: {', '.join(item.dependencies)}]"
                        if item.assigned_uid:
                            status_info += f" [assigned to: {item.assigned_uid}]"
                        lines.append(status_info)
                    if len(items) > 5:
                        lines.append(f"    ... and {len(items) - 5} more")

        return "\n".join(lines)

    @staticmethod
    def _get_orchestrator_behavior_message() -> str:
        """Fixed orchestrator behavior instructions."""
        return """You are an orchestrator agent that coordinates work execution.

Your responsibilities:
1. Analyze incoming tasks and create detailed work plans
2. Identify which parts can be done locally vs need delegation
3. Assign work to appropriate adjacent nodes based on their capabilities
4. Monitor progress and handle responses
5. Synthesize results when work is complete

Guidelines:
- Break complex tasks into manageable work items
- Consider dependencies between items
- Match work to node capabilities
- Delegate when adjacent nodes have better tools/skills
- Track all delegated work via correlation IDs
- Update work plan status as responses arrive"""

    def _build_complete_system_message(self) -> str:
        """Build complete system message combining behavior + specialization."""
        behavior_msg = self._get_orchestrator_behavior_message()
        
        if self.domain_specialization:
            # User provided domain specialization
            return f"{behavior_msg}\n\nDomain Specialization:\n{self.domain_specialization}"
        else:
            # No specialization provided
            return behavior_msg
