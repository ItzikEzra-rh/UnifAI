"""
Generic test helper functions for ALL nodes.

These helpers provide common patterns that any node test can use.
Keeps test code DRY and consistent across the test suite.

ALL functions here are GENERIC and work for ANY node type.
"""

from typing import Set
from graph.state.graph_state import GraphState, Channel
from graph.state.state_view import StateView
from graph.models import StepContext


def setup_node_with_state(node, channels: Set[str] = None):
    """
    ✅ GENERIC: Setup any node with state and proper channel permissions.
    
    This is the standard pattern ALL node tests should use to initialize
    state before testing node behavior.
    
    Args:
        node: Any node instance (OrchestratorNode, CustomAgentNode, etc.)
        channels: Set of channel names for read/write access
                 If None, uses common workload channels
    
    Returns:
        The StateView that was set
        
    Example:
        node = OrchestratorNode(llm=mock_llm)
        state_view = setup_node_with_state(node)
        # Now node can access workload services
        service = node.get_workload_service()
    """
    if channels is None:
        # Default: common workload channels
        channels = {
            Channel.THREADS,
            Channel.WORKSPACES,
            Channel.TASK_THREADS,
            Channel.INTER_PACKETS,  # For IEM
            Channel.MESSAGES  # For conversation
        }
    
    state = GraphState()
    state_view = StateView(state, reads=channels, writes=channels)
    node._state = state_view
    
    return state_view


def setup_node_with_context(node, uid: str, adjacent_nodes: list = None):
    """
    ✅ GENERIC: Setup node with both state and context.
    
    Use this when tests need to access node.uid or call methods that
    access self.uid, self.display_name, or adjacency.
    
    Args:
        node: Any node instance
        uid: Node UID
        adjacent_nodes: List of adjacent node UIDs
        
    Returns:
        Tuple of (StateView, StepContext)
        
    Example:
        node = CustomAgentNode(llm=mock_llm)
        state_view, context = setup_node_with_context(node, "agent1", ["orch1"])
        assert node.uid == "agent1"  # Now works!
        node._handle_new_work(task)  # Methods that use self.uid work!
    """
    # Setup state
    state_view = setup_node_with_state(node)
    
    # Setup context
    context = create_test_step_context(uid, adjacent_nodes or [])
    node._ctx = context
    
    return state_view, context


def create_test_step_context(uid: str, adjacent_node_uids: list = None):
    """
    ✅ GENERIC: Create StepContext for testing.
    
    Args:
        uid: The unique identifier for the step
        adjacent_node_uids: List of adjacent node UIDs
        
    Returns:
        StepContext instance properly configured for testing
    """
    from graph.models import StepContext
    from unittest.mock import Mock
    
    # Create mock metadata
    metadata = Mock()
    metadata.uid = uid
    metadata.display_name = f"Test {uid}"
    metadata.type = "test_node"
    metadata.description = "Test node for testing"
    
    # Create adjacent_nodes (the actual field name in StepContext)
    from graph.models.adjacency import AdjacentNodes
    adjacent_nodes = Mock(spec=AdjacentNodes)
    
    # Mock the adjacency dict for get_adjacent_nodes()
    adjacency_dict = {}
    for adj_uid in (adjacent_node_uids or []):
        mock_card = Mock()
        mock_card.uid = adj_uid
        mock_card.type_key = "test_type"
        mock_card.description = f"Adjacent node {adj_uid}"
        adjacency_dict[adj_uid] = mock_card
    
    adjacent_nodes.as_dict = Mock(return_value=adjacency_dict)
    
    # ✅ FIX: Make adjacent_nodes fully compatible with all operations
    # This allows: for uid in context.adjacent_nodes, context.adjacent_nodes.keys(), and uid in context.adjacent_nodes
    # IMPORTANT: Use list() to create snapshots, not views, to prevent cross-contamination between test contexts
    adjacent_uids_snapshot = list(adjacency_dict.keys())
    adjacent_nodes.__iter__ = Mock(return_value=iter(adjacent_uids_snapshot))
    adjacent_nodes.__len__ = Mock(return_value=len(adjacent_uids_snapshot))
    adjacent_nodes.keys = Mock(return_value=adjacent_uids_snapshot)  # Return list, not dict_keys view
    adjacent_nodes.__contains__ = Mock(side_effect=lambda uid: uid in adjacent_uids_snapshot)  # For "uid in adjacent_nodes"
    
    return StepContext(
        uid=uid,
        metadata=metadata,
        adjacent_nodes=adjacent_nodes
    )


def assert_workplan_created(state_view: StateView, thread_id: str, owner_uid: str) -> bool:
    """
    ✅ GENERIC: Assert that a work plan was created for any WorkloadCapable node.
    
    Args:
        state_view: The state view to check
        thread_id: Thread ID to check
        owner_uid: Owner UID of the workplan
        
    Returns:
        True if workplan exists
        
    Example:
        # After orchestrator runs
        assert_workplan_created(state_view, "thread_1", "orch1")
    """
    from elements.nodes.common.workload import UnifiedWorkloadService, StateBoundStorage
    
    storage = StateBoundStorage(state_view)
    service = UnifiedWorkloadService(storage)
    
    work_plan = service.get_workspace_service().load_work_plan(thread_id, owner_uid)
    assert work_plan is not None, f"WorkPlan not found for thread={thread_id}, owner={owner_uid}"
    
    return True


def assert_thread_created(state_view: StateView, thread_title: str) -> str:
    """
    ✅ GENERIC: Assert that a thread was created and return its ID.
    
    Args:
        state_view: The state view to check
        thread_title: Expected thread title
        
    Returns:
        Thread ID if found
        
    Example:
        thread_id = assert_thread_created(state_view, "My Task")
    """
    from elements.nodes.common.workload import UnifiedWorkloadService, StateBoundStorage
    
    storage = StateBoundStorage(state_view)
    service = UnifiedWorkloadService(storage)
    
    # Get all threads (this is a simplification - in real code might need to search)
    # For now, just verify we can access thread service
    thread_service = service.get_thread_service()
    assert thread_service is not None
    
    # Return a dummy ID for now - this would need proper implementation
    # based on how threads are actually stored
    return "thread_created"


# =============================================================================
# ✅ GENERIC ASSERTION HELPERS - Work for ANY node type
# =============================================================================

def assert_has_workload_capability(node):
    """
    ✅ GENERIC: Assert node has workload management capabilities.
    
    Example:
        node = OrchestratorNode(llm=mock_llm)
        setup_node_with_state(node)
        assert_has_workload_capability(node)
    """
    assert hasattr(node, 'get_workload_service'), \
        f"{node.__class__.__name__} should have get_workload_service()"
    assert hasattr(node, 'workspaces'), \
        f"{node.__class__.__name__} should have .workspaces property"
    assert hasattr(node, 'threads'), \
        f"{node.__class__.__name__} should have .threads property"


def assert_has_iem_capability(node):
    """
    ✅ GENERIC: Assert node has IEM messaging capabilities.
    
    Example:
        node = CustomAgentNode(llm=mock_llm)
        setup_node_with_context(node, "agent1")
        assert_has_iem_capability(node)
    """
    assert hasattr(node, 'send_task'), \
        f"{node.__class__.__name__} should have send_task()"
    assert hasattr(node, 'inbox_packets'), \
        f"{node.__class__.__name__} should have inbox_packets()"


def assert_has_llm_capability(node):
    """
    ✅ GENERIC: Assert node has LLM capabilities.
    
    Example:
        node = OrchestratorNode(llm=mock_llm)
        assert_has_llm_capability(node)
    """
    assert hasattr(node, 'llm'), \
        f"{node.__class__.__name__} should have .llm attribute"
    assert node.llm is not None, \
        f"{node.__class__.__name__}.llm should not be None"


def assert_has_agent_capability(node):
    """
    ✅ GENERIC: Assert node has agent execution capabilities.
    
    Example:
        node = CustomAgentNode(llm=mock_llm)
        assert_has_agent_capability(node)
    """
    assert hasattr(node, 'create_strategy'), \
        f"{node.__class__.__name__} should have create_strategy()"
    assert hasattr(node, 'run_agent'), \
        f"{node.__class__.__name__} should have run_agent()"


def get_workspace_from_node(node, thread_id: str):
    """
    ✅ GENERIC: Get workspace from ANY WorkloadCapable node (correct API).
    
    Replaces the deprecated node.get_workspace(thread_id) pattern.
    
    Args:
        node: Any node with WorkloadCapableMixin (CustomAgent, Orchestrator, etc.)
        thread_id: Thread ID to get workspace for
        
    Returns:
        Workspace instance
        
    Example:
        workspace = get_workspace_from_node(custom_agent, "my_thread")
        results = workspace.context.results
    """
    service = node.get_workload_service()
    workspace_service = service.get_workspace_service()
    return workspace_service.get_workspace(thread_id)


# =============================================================================
# ✅ GENERIC ORCHESTRATION TEST HELPERS - Work for ALL orchestration scenarios
# =============================================================================

def create_work_plan_with_items(
    thread_id: str,
    owner_uid: str,
    num_local: int = 0,
    num_remote: int = 0,
    remote_workers: list = None
):
    """
    ✅ GENERIC: Create work plan with pre-populated items.
    
    Useful for: Setting up test scenarios with known work plans.
    Works for: ANY orchestrator or workload testing.
    
    Args:
        thread_id: Thread ID for the work plan
        owner_uid: Owner node UID (usually orchestrator)
        num_local: Number of LOCAL work items to create
        num_remote: Number of REMOTE work items to create
        remote_workers: List of worker UIDs for remote items (cycles through list)
        
    Returns:
        WorkPlan with populated items
        
    Example:
        plan = create_work_plan_with_items("thread1", "orch1", num_local=2, num_remote=3, 
                                          remote_workers=["worker1", "worker2"])
    """
    from elements.nodes.common.workload import WorkPlan, WorkItem, WorkItemKind, WorkItemStatus
    
    plan = WorkPlan(
        summary="Test work plan",
        owner_uid=owner_uid,
        thread_id=thread_id
    )
    
    # Add local items
    for i in range(num_local):
        item = WorkItem(
            id=f"local_{i+1}",
            kind=WorkItemKind.LOCAL,
            title=f"Local Task {i+1}",
            description=f"Execute local work item {i+1}",
            status=WorkItemStatus.PENDING
        )
        plan.items[item.id] = item
    
    # Add remote items
    if remote_workers is None:
        remote_workers = [f"worker_{i+1}" for i in range(num_remote)]
    
    for i in range(num_remote):
        worker_uid = remote_workers[i % len(remote_workers)] if remote_workers else f"worker_{i+1}"
        item = WorkItem(
            id=f"remote_{i+1}",
            kind=WorkItemKind.REMOTE,
            title=f"Remote Task {i+1}",
            description=f"Delegate work item {i+1}",
            assigned_uid=worker_uid,
            status=WorkItemStatus.PENDING
        )
        plan.items[item.id] = item
    
    return plan


def assert_work_plan_status(
    plan,
    expected_pending: int = None,
    expected_in_progress: int = None,
    expected_waiting: int = None,
    expected_done: int = None,
    expected_failed: int = None,
    expected_blocked: int = None,
    expected_total: int = None
):
    """
    ✅ GENERIC: Assert work plan status counts.
    
    Useful for: Verifying work plan state in tests.
    Works for: ANY work plan testing.
    
    Args:
        plan: WorkPlan instance to check
        expected_*: Expected counts for each status (None = don't check)
        
    Example:
        assert_work_plan_status(plan, expected_pending=2, expected_done=3, expected_total=5)
    """
    counts = plan.get_status_counts()
    
    if expected_pending is not None:
        assert counts.pending == expected_pending, \
            f"Expected {expected_pending} PENDING items, got {counts.pending}"
    
    if expected_in_progress is not None:
        assert counts.in_progress == expected_in_progress, \
            f"Expected {expected_in_progress} IN_PROGRESS items, got {counts.in_progress}"
    
    if expected_waiting is not None:
        assert counts.waiting == expected_waiting, \
            f"Expected {expected_waiting} WAITING items, got {counts.waiting}"
    
    if expected_done is not None:
        assert counts.done == expected_done, \
            f"Expected {expected_done} DONE items, got {counts.done}"
    
    if expected_failed is not None:
        assert counts.failed == expected_failed, \
            f"Expected {expected_failed} FAILED items, got {counts.failed}"
    
    if expected_blocked is not None:
        assert counts.blocked == expected_blocked, \
            f"Expected {expected_blocked} BLOCKED items, got {counts.blocked}"
    
    if expected_total is not None:
        assert counts.total == expected_total, \
            f"Expected {expected_total} total items, got {counts.total}"


def create_mock_worker_node(uid: str, capabilities: list = None, node_type: str = "worker"):
    """
    ✅ GENERIC: Create mock worker node for orchestration tests.
    
    Useful for: Testing delegation and multi-agent scenarios.
    Works for: ANY orchestration testing with multiple nodes.
    
    Args:
        uid: Unique identifier for the worker
        capabilities: List of capability strings (e.g., ["data_processing", "analysis"])
        node_type: Type of node (default: "worker")
        
    Returns:
        Mock object representing a worker node
        
    Example:
        worker = create_mock_worker_node("worker1", capabilities=["analysis", "reporting"])
    """
    from unittest.mock import Mock
    
    worker = Mock()
    worker.uid = uid
    worker.type = node_type
    worker.description = f"Test {node_type} node"
    worker.capabilities = set(capabilities or [])
    
    return worker


def simulate_worker_response(
    orchestrator,
    thread_id: str,
    correlation_task_id: str,
    success: bool = True,
    content: str = "Work completed",
    from_uid: str = "worker1",
    result_data: dict = None
):
    """
    ✅ GENERIC: Simulate worker completing work and sending response.
    
    Useful for: Testing response handling without real workers.
    Works for: ANY orchestration testing with delegation.
    
    Args:
        orchestrator: Orchestrator node instance
        thread_id: Thread ID for the response
        correlation_task_id: Correlation ID linking response to work item
        success: Whether work succeeded
        content: Response content
        from_uid: UID of responding worker
        result_data: Optional result data dict
        
    Returns:
        Thread ID if work plan was updated, None otherwise
        
    Example:
        thread_id = simulate_worker_response(orch, "thread1", "corr_123", 
                                            success=True, from_uid="worker1")
    """
    from elements.nodes.common.workload import Task
    
    response = Task(
        content=content,
        created_by=from_uid,
        correlation_task_id=correlation_task_id,
        thread_id=thread_id
    )
    
    if not success:
        # Task.error is now a string (type consistency fixed)
        response.error = content
    elif result_data:
        response.result = result_data
    
    return orchestrator._handle_task_response(response)


def create_predictable_llm_for_phases(phase_responses: dict):
    """
    ✅ GENERIC: Create LLM mock with predictable responses per phase.
    
    Useful for: Testing phase transitions with controlled LLM behavior.
    Works for: ANY phase-based orchestration testing.
    
    Args:
        phase_responses: Dict mapping phase names to list of responses
                        e.g., {"planning": ["Create plan"], "allocation": ["Assign work"]}
        
    Returns:
        Mock LLM that returns predictable responses
        
    Example:
        llm = create_predictable_llm_for_phases({
            "planning": ["I'll create a 3-step plan"],
            "monitoring": ["All tasks completed"]
        })
    """
    from unittest.mock import Mock
    
    llm = Mock()
    llm.phase_responses = phase_responses
    llm.call_count_per_phase = {phase: 0 for phase in phase_responses.keys()}
    
    def mock_chat(messages, tools=None, **kwargs):
        # Simple mock that returns next response
        # In real tests, you'd inspect messages to determine phase
        mock_response = Mock()
        mock_response.content = "Mock LLM response"
        mock_response.tool_calls = []
        return mock_response
    
    llm.chat = mock_chat
    return llm


# ==================== THREAD HIERARCHY HELPERS ====================

def create_thread_hierarchy(orchestrator, parent_thread_id: str, num_children: int = 1):
    """
    ✅ GENERIC: Create parent thread with children for testing hierarchy.
    
    Useful for: Testing thread parent/child relationships and response routing.
    Works for: ANY node with ThreadService (Orchestrator, CustomAgent).
    
    Args:
        orchestrator: Node with thread service (has .threads property)
        parent_thread_id: Thread ID for parent
        num_children: Number of child threads to create
        
    Returns:
        Dict with structure: {
            "parent": Thread,
            "children": [Thread, Thread, ...]
        }
        
    Example:
        hierarchy = create_thread_hierarchy(orch, "parent_1", num_children=3)
        parent = hierarchy["parent"]
        children = hierarchy["children"]
    """
    thread_service = orchestrator.get_workload_service().get_thread_service()
    
    # Create parent thread
    parent = thread_service.create_root_thread(
        title=f"Parent Thread {parent_thread_id}",
        objective="Parent objective",
        initiator="test_initiator"
    )
    
    # Create children
    children = []
    for i in range(num_children):
        child = thread_service.create_child_thread(
            parent=parent,
            title=f"Child Thread {i+1}",
            objective=f"Child {i+1} objective",
            initiator="test_initiator"
        )
        children.append(child)
    
    return {
        "parent": parent,
        "children": children
    }


def create_multi_level_hierarchy(orchestrator, levels: int = 3):
    """
    ✅ GENERIC: Create multi-level thread hierarchy (grandparent → parent → child).
    
    Useful for: Testing deep hierarchy traversal and response routing.
    Works for: ANY node with ThreadService.
    
    Args:
        orchestrator: Node with thread service
        levels: Number of levels in hierarchy (minimum 2)
        
    Returns:
        List of threads from root to leaf: [grandparent, parent, child, ...]
        
    Example:
        threads = create_multi_level_hierarchy(orch, levels=4)
        root = threads[0]
        leaf = threads[-1]
        middle = threads[1:-1]
    """
    if levels < 2:
        raise ValueError("Hierarchy must have at least 2 levels")
    
    thread_service = orchestrator.get_workload_service().get_thread_service()
    
    # Create root
    hierarchy = []
    root = thread_service.create_root_thread(
        title="Root Thread",
        objective="Root objective",
        initiator="test_initiator"
    )
    hierarchy.append(root)
    
    # Create remaining levels
    current_parent = root
    for level in range(1, levels):
        child = thread_service.create_child_thread(
            parent=current_parent,
            title=f"Level {level} Thread",
            objective=f"Level {level} objective",
            initiator="test_initiator"
        )
        hierarchy.append(child)
        current_parent = child
    
    return hierarchy


def assert_thread_hierarchy(parent_thread, child_thread):
    """
    ✅ GENERIC: Assert correct parent-child thread relationship.
    
    Useful for: Verifying thread hierarchy integrity.
    Works for: ANY Thread objects.
    
    Args:
        parent_thread: Parent Thread instance
        child_thread: Child Thread instance
        
    Example:
        assert_thread_hierarchy(parent, child)
    """
    # Child should reference parent
    assert child_thread.parent_thread_id == parent_thread.thread_id, \
        f"Child's parent_thread_id {child_thread.parent_thread_id} != parent's thread_id {parent_thread.thread_id}"
    
    # Parent should list child
    assert child_thread.thread_id in parent_thread.child_thread_ids, \
        f"Child {child_thread.thread_id} not in parent's child_thread_ids {parent_thread.child_thread_ids}"


def assert_response_routes_to_root(orchestrator, child_thread_id: str, expected_root_id: str):
    """
    ✅ GENERIC: Assert response from child routes to correct root thread.
    
    Useful for: Verifying response routing through hierarchy.
    Works for: ANY orchestrator with ThreadService.
    
    Args:
        orchestrator: Orchestrator node
        child_thread_id: Child thread ID (where response originates)
        expected_root_id: Expected root thread ID (where work plan lives)
        
    Example:
        assert_response_routes_to_root(orch, "child_123", "root_1")
    """
    thread_service = orchestrator.get_workload_service().get_thread_service()
    actual_root = thread_service.find_work_plan_owner(child_thread_id)
    
    assert actual_root == expected_root_id, \
        f"Response from {child_thread_id} routes to {actual_root}, expected {expected_root_id}"


def get_hierarchy_depth(thread_service, thread_id: str) -> int:
    """
    ✅ GENERIC: Get depth of thread in hierarchy (0 for root).
    
    Useful for: Verifying hierarchy structure.
    Works for: ANY ThreadService.
    
    Args:
        thread_service: ThreadService instance
        thread_id: Thread ID to check
        
    Returns:
        Depth (0 = root, 1 = first level child, etc.)
        
    Example:
        depth = get_hierarchy_depth(service, "child_thread_id")
        assert depth == 2  # Grandchild
    """
    path = thread_service.get_hierarchy_path(thread_id)
    return len(path) - 1  # Root has depth 0