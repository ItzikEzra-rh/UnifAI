"""
WorkPlan and WorkItem models for orchestration.

Provides Pydantic-based models for work planning and execution tracking.
Includes comprehensive dependency management and status tracking.
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Set, Any
from datetime import datetime
from enum import Enum
import uuid
import threading
from collections import defaultdict


class WorkItemStatus(str, Enum):
    """
    Status of a work item.
    
    Status Semantics:
    - PENDING: Not yet assigned or started
    - IN_PROGRESS: Being executed (local) or delegated (remote)
      * For LOCAL items: Currently executing locally
      * For REMOTE items: Delegated and waiting for response
    - DONE: Successfully completed
    - FAILED: Failed after retries
    """
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    FAILED = "failed"


class WorkItemKind(str, Enum):
    """Kind of work item execution."""
    LOCAL = "local"    # Execute locally on this node
    REMOTE = "remote"  # Delegate to adjacent node


class ToolArguments(BaseModel):
    """Dynamic tool arguments for work items."""
    
    class Config:
        extra = "allow"  # Allow arbitrary additional fields
    
    def __init__(self, data: Optional[Dict[str, Any]] = None, **kwargs):
        """Initialize with either a dict or keyword arguments."""
        if data is not None:
            if kwargs:
                raise ValueError("Cannot provide both 'data' dict and keyword arguments")
            super().__init__(**data)
        else:
            super().__init__(**kwargs)
    
    def __len__(self) -> int:
        """Return the number of arguments."""
        return len(self.__dict__)
    
    def __getitem__(self, key: str) -> Any:
        """Allow dict-like access."""
        return getattr(self, key)
    
    def __setitem__(self, key: str, value: Any) -> None:
        """Allow dict-like assignment."""
        setattr(self, key, value)
    
    def __contains__(self, key: str) -> bool:
        """Check if key exists."""
        return hasattr(self, key)


class LocalExecution(BaseModel):
    """
    Local work execution record (for LOCAL work items).
    
    Captures what the orchestrator did directly without delegation.
    Includes reasoning, actions taken, and outcome.
    """
    reasoning: Optional[str] = Field(None, description="Why this approach was taken")
    actions_taken: Optional[str] = Field(None, description="What was done (tools used, analysis performed)")
    outcome: Optional[str] = Field(None, description="Result of the execution")
    tools_used: List[str] = Field(default_factory=list, description="Tools invoked during execution")
    executed_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="When execution completed")


class DelegationExchange(BaseModel):
    """
    Complete request-response exchange in a delegation conversation.
    
    Represents one complete turn: orchestrator asks → agent responds.
    Multiple exchanges form a multi-turn conversation.
    """
    # Ordering and identification
    sequence: int = Field(..., description="Turn number in conversation (0=first, 1=second, etc.)")
    task_id: str = Field(..., description="Unique task ID for this delegation")
    
    # Request side (what orchestrator asked)
    query: str = Field(..., description="What was specifically asked/delegated")
    delegated_to: str = Field(..., description="UID of agent this was delegated to")
    delegated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="When delegation was sent")
    
    # Response side (what agent answered)
    response_content: Optional[str] = Field(None, description="Agent's response text")
    response_data: Optional[Dict[str, Any]] = Field(None, description="Structured data (AgentResult, etc.)")
    responded_by: Optional[str] = Field(None, description="Who responded (usually same as delegated_to)")
    responded_at: Optional[str] = Field(None, description="When response was received")
    
    # State tracking
    processed: bool = Field(default=False, description="Whether LLM has acted on this response (re-delegated or marked status)")
    
    @property
    def is_pending(self) -> bool:
        """Check if waiting for response."""
        return self.response_content is None
    
    @property
    def needs_attention(self) -> bool:
        """Check if has response but LLM hasn't acted on it yet."""
        return self.response_content is not None and not self.processed


class WorkItemResult(BaseModel):
    """
    Complete result container for both LOCAL and REMOTE work items.
    
    Design: Unified model that adapts based on work item kind.
    - REMOTE items: Use 'delegations' list to track conversation history
    - LOCAL items: Use 'local_execution' to record direct execution
    
    This follows SOLID principles: single model, different fields populated.
    """
    # For REMOTE items: delegation conversation history
    delegations: List[DelegationExchange] = Field(
        default_factory=list,
        description="Delegation conversation history (REMOTE items only). Empty for LOCAL items."
    )
    
    # For LOCAL items: execution record
    local_execution: Optional[LocalExecution] = Field(
        None, 
        description="Local execution details (LOCAL items only). None for REMOTE items."
    )
    
    # Common fields (both LOCAL and REMOTE)
    success: bool = Field(default=False, description="Final success status (set when marked DONE)")
    final_summary: Optional[str] = Field(None, description="Final synthesized result or conclusion")
    data: Optional[Dict[str, Any]] = Field(None, description="Structured result data")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    artifacts: List[str] = Field(default_factory=list, description="List of created artifacts")
    
    @property
    def pending_exchange(self) -> Optional[DelegationExchange]:
        """Get the currently pending delegation exchange (waiting for response), if any."""
        for ex in reversed(self.delegations):  # Check most recent first
            if ex.is_pending:
                return ex
        return None
    
    @property
    def latest_exchange(self) -> Optional[DelegationExchange]:
        """Get the most recent delegation exchange."""
        return self.delegations[-1] if self.delegations else None
    
    @property
    def has_unprocessed_responses(self) -> bool:
        """Check if any delegation responses need LLM interpretation."""
        return any(ex.needs_attention for ex in self.delegations)
    
    @property
    def conversation_summary(self) -> str:
        """
        Format delegation history with state indicators for LLM interpretation.
        
        Shows clear indicators of what needs attention vs what's been handled.
        Helps LLM understand conversation state and decide next actions.
        
        Returns:
            Formatted string with conversation history and state indicators
        """
        if not self.delegations:
            return ""
        
        # Single exchange: simple format
        if len(self.delegations) == 1:
            ex = self.delegations[0]
            if ex.is_pending:
                return f"⏳ WAITING for response from {ex.delegated_to}"
            elif ex.needs_attention:
                return f"🔔 NEW RESPONSE from {ex.responded_by} (needs your interpretation):\n  {ex.response_content}"
            else:
                return f"✓ Response from {ex.responded_by} (processed):\n  {ex.response_content}"
        
        # Multi-turn conversation: detailed format
        lines = [f"Conversation History ({len(self.delegations)} turns):"]
        for ex in self.delegations:
            if ex.is_pending:
                lines.append(f"  [{ex.sequence}] ⏳ WAITING: Query sent to {ex.delegated_to}")
                lines.append(f"      Query: {ex.query}")
            elif ex.needs_attention:
                lines.append(f"  [{ex.sequence}] 🔔 NEW: Response from {ex.responded_by} (needs interpretation)")
                lines.append(f"      Query: {ex.query}")
                preview = ex.response_content[:100] + "..." if len(ex.response_content) > 100 else ex.response_content
                lines.append(f"      Response: {preview}")
            else:
                lines.append(f"  [{ex.sequence}] ✓ PROCESSED: {ex.responded_by}")
                preview = ex.response_content[:80] + "..." if len(ex.response_content) > 80 else ex.response_content
                lines.append(f"      Response: {preview}")
        
        return "\n".join(lines)


class WorkItem(BaseModel):
    """A single work item in a work plan."""
    
    # Core identification
    id: str = Field(..., description="Unique identifier for this work item")
    title: str = Field(..., description="Short, descriptive title")
    description: str = Field(..., description="Detailed description of the work")
    
    # Dependencies and execution
    dependencies: List[str] = Field(default_factory=list, description="Work item IDs that must complete first")
    status: WorkItemStatus = Field(default=WorkItemStatus.PENDING, description="Current status")
    kind: WorkItemKind = Field(default=WorkItemKind.LOCAL, description="Local or remote execution")
    
    # Assignment and execution details
    assigned_uid: Optional[str] = Field(None, description="UID of assigned node")
    tool: Optional[str] = Field(None, description="Tool to use for execution")
    args: ToolArguments = Field(default_factory=ToolArguments, description="Tool arguments")
    
    # Results and tracking
    result: Optional[WorkItemResult] = Field(None, description="Execution result")
    error: Optional[str] = Field(None, description="Error message if failed")
    child_thread_id: Optional[str] = Field(None, description="Child thread ID for re-delegation context continuity")
    retry_count: int = Field(default=0, description="Number of retry attempts")
    max_retries: int = Field(default=3, description="Maximum retry attempts before marking as failed")
    
    # Timestamps
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def is_ready_for_execution(self, completed_item_ids: Set[str]) -> bool:
        """Check if this item is ready for execution based on dependencies."""
        if self.status != WorkItemStatus.PENDING:
            return False
        
        # All dependencies must be completed
        for dep_id in self.dependencies:
            if dep_id not in completed_item_ids:
                return False
        
        return True
    
    def is_blocked(self, completed_item_ids: Set[str]) -> bool:
        """Check if this item is blocked by incomplete dependencies."""
        if self.status != WorkItemStatus.PENDING:
            return False
        
        # Check if any dependencies are not completed
        for dep_id in self.dependencies:
            if dep_id not in completed_item_ids:
                return True
        
        return False
    
    def can_retry(self) -> bool:
        """Check if this item can be retried."""
        from .retry_policy import RetryPolicyService
        return RetryPolicyService.can_retry(self)
    
    def increment_retry(self) -> bool:
        """
        Increment retry count and mark as updated.
        
        Returns:
            True if increment was successful, False if max retries exceeded
        """
        from .retry_policy import RetryPolicyService
        return RetryPolicyService.increment_retry(self)
    
    def has_unprocessed_responses(self) -> bool:
        """
        Check if this work item has unprocessed responses needing LLM action.
        
        Returns True only if:
        - Item is IN_PROGRESS (actively being worked on)
        - Item is REMOTE (delegated to another agent)
        - Item has result with delegations
        - At least one delegation response is unprocessed
        
        This is the canonical check for "orchestrator needs to act on this item's responses"
        """
        return (
            self.status == WorkItemStatus.IN_PROGRESS 
            and self.kind == WorkItemKind.REMOTE
            and self.result is not None
            and self.result.has_unprocessed_responses
        )
    
    def mark_updated(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = datetime.utcnow().isoformat()


class WorkItemStatusCounts(BaseModel):
    """
    Count of work items by status.
    
    Note: 'waiting' is removed - use in_progress with kind=REMOTE instead.
    'blocked' is a computed metric (PENDING items with incomplete dependencies).
    """
    pending: int = 0
    in_progress: int = 0
    done: int = 0
    failed: int = 0
    blocked: int = 0
    
    @property
    def total(self) -> int:
        """Total count of all items."""
        return self.pending + self.in_progress + self.done + self.failed + self.blocked


class WorkPlanStatusSummary(BaseModel):
    """
    Summary of work plan status.
    
    Note: waiting_items is kept for backward compatibility but is now
    calculated as (IN_PROGRESS items where kind=REMOTE). The actual
    status for these items is IN_PROGRESS.
    """
    exists: bool = False
    total_items: int = 0
    pending_items: int = 0
    in_progress_items: int = 0
    waiting_items: int = 0  # Calculated: IN_PROGRESS + kind=REMOTE
    done_items: int = 0
    failed_items: int = 0
    blocked_items: int = 0
    has_local_ready: bool = False
    has_remote_ready: bool = False  # True if any PENDING + kind=REMOTE items with dependencies met
    has_remote_waiting: bool = False  # True if any IN_PROGRESS + kind=REMOTE items exist
    has_responses: bool = False  # True if any IN_PROGRESS + kind=REMOTE items have result with delegations
    is_complete: bool = False


class WorkPlan(BaseModel):
    """A work plan containing multiple work items."""
    
    # Core identification
    summary: str = Field(..., description="High-level summary of the work plan")
    owner_uid: str = Field(..., description="UID of the node that owns this plan")
    thread_id: str = Field(..., description="Thread ID this plan belongs to")
    
    # Work items
    items: Dict[str, WorkItem] = Field(default_factory=dict, description="Work items by ID")
    
    # Timestamps
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    
    @property
    def total_items(self) -> int:
        """Get the total number of work items in this plan."""
        return len(self.items)
    
    def get_completed_item_ids(self) -> Set[str]:
        """
        Get IDs of successfully completed items (DONE only).
        
        Note: FAILED items are NOT considered completed for dependency resolution.
        Items depending on FAILED items will be blocked until the dependency is
        retried successfully or the dependent item is explicitly marked as FAILED.
        
        This prevents cascade cycles where items appear "ready" but actually
        cannot proceed due to missing dependency results.
        """
        completed = set()
        for item_id, item in self.items.items():
            if item.status == WorkItemStatus.DONE:
                completed.add(item_id)
        return completed
    
    def get_failed_item_ids(self) -> Set[str]:
        """Get IDs of failed items."""
        failed = set()
        for item_id, item in self.items.items():
            if item.status == WorkItemStatus.FAILED:
                failed.add(item_id)
        return failed
    
    def get_ready_items(self) -> List[WorkItem]:
        """Get items that are ready for execution (dependencies satisfied)."""
        completed_ids = self.get_completed_item_ids()
        ready_items = []
        
        for item in self.items.values():
            if item.is_ready_for_execution(completed_ids):
                ready_items.append(item)
        
        return ready_items
    
    def get_blocked_items(self) -> List[WorkItem]:
        """Get items that are blocked by incomplete dependencies."""
        completed_ids = self.get_completed_item_ids()
        blocked_items = []
        
        for item in self.items.values():
            if item.is_blocked(completed_ids):
                blocked_items.append(item)
        
        return blocked_items
    
    def get_items_blocked_by_failure(self) -> List[WorkItem]:
        """
        Get items that are blocked specifically by failed dependencies.
        
        These items are PENDING but cannot proceed because one or more
        of their dependencies has FAILED. They need special handling:
        either retry the failed dependency or mark these items as failed too.
        """
        completed_ids = self.get_completed_item_ids()
        failed_ids = self.get_failed_item_ids()
        blocked_by_failure = []
        
        for item in self.items.values():
            if item.status == WorkItemStatus.PENDING:
                # Check if any dependencies are failed
                has_failed_dep = any(dep_id in failed_ids for dep_id in item.dependencies)
                # And item is blocked (not all deps are DONE)
                is_blocked = item.is_blocked(completed_ids)
                
                if has_failed_dep and is_blocked:
                    blocked_by_failure.append(item)
        
        return blocked_by_failure
    
    def get_items_by_status(self, status: WorkItemStatus) -> List[WorkItem]:
        """Get all items with the specified status."""
        return [item for item in self.items.values() if item.status == status]
    
    def get_status_counts(self) -> WorkItemStatusCounts:
        """
        Get count of items by status.
        
        Note: WAITING status is removed. Items that were WAITING are now IN_PROGRESS
        with kind=REMOTE. Use get_status_summary() to get waiting_items count.
        """
        counts = WorkItemStatusCounts()
        completed_ids = self.get_completed_item_ids()
        
        for item in self.items.values():
            if item.status == WorkItemStatus.PENDING:
                if item.is_blocked(completed_ids):
                    counts.blocked += 1
                else:
                    counts.pending += 1
            elif item.status == WorkItemStatus.IN_PROGRESS:
                counts.in_progress += 1
            elif item.status == WorkItemStatus.DONE:
                counts.done += 1
            elif item.status == WorkItemStatus.FAILED:
                counts.failed += 1
        
        return counts
    
    def is_complete(self) -> bool:
        """Check if all work items are complete (DONE or FAILED)."""
        if not self.items:
            return False
        
        for item in self.items.values():
            if item.status not in [WorkItemStatus.DONE, WorkItemStatus.FAILED]:
                return False
        
        return True
    
    def mark_updated(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = datetime.utcnow().isoformat()


class WorkPlanService:
    """
    Domain service for WorkPlan operations.
    
    SOLID design: Handles all work plan business logic and workspace access.
    Directly manages work plans stored in workspace.context.work_plans field.
    
    Responsibilities:
    - Work plan CRUD operations (create, load, save, remove)
    - Business logic (status transitions, delegation, response ingestion)
    - Thread-safe atomic updates with per-plan locking
    - Direct workspace access for work plan data management
    
    Thread-safe: Uses RLock per (thread_id, owner_uid) to prevent race conditions.
    """
    
    # Class-level lock registry to ensure same lock instance per workplan
    _locks: Dict[str, threading.RLock] = defaultdict(threading.RLock)
    _locks_lock = threading.Lock()  # Protects the locks dictionary itself
    
    def __init__(self, workspace_service, thread_service):
        """
        Initialize with focused service dependencies.
        
        Args:
            workspace_service: IWorkspaceService for workspace operations
            thread_service: IThreadService for thread hierarchy operations
        """
        self._workspace_service = workspace_service
        self._thread_service = thread_service
    
    def _get_lock(self, thread_id: str, owner_uid: str) -> threading.RLock:
        """Get or create a lock for the specific workplan."""
        lock_key = f"{thread_id}:{owner_uid}"
        with self._locks_lock:
            return self._locks[lock_key]
    
    def with_lock(self, thread_id: str, owner_uid: str):
        """Context manager for thread-safe workplan operations."""
        return self._get_lock(thread_id, owner_uid)
    
    def create(self, thread_id: str, owner_uid: str) -> WorkPlan:
        """Create a new work plan."""
        plan = WorkPlan(
            summary="New Work Plan",
            owner_uid=owner_uid,
            thread_id=thread_id
        )
        return plan
    
    def load(self, thread_id: str, owner_uid: str) -> Optional[WorkPlan]:
        """Load work plan from dedicated workspace field."""
        try:
            workspace = self._workspace_service.get_workspace(thread_id)
            plan_data = workspace.context.work_plans.get(owner_uid)
            
            if plan_data:
                plan = WorkPlan(**plan_data)
                return plan
            
            return None
        except Exception as e:
            print(f"❌ [PLAN] Error loading: {e}")
            return None
    
    def load_for_response(self, response_thread_id: str, owner_uid: str) -> Optional[WorkPlan]:
        """
        Load work plan for response processing.
        
        Automatically resolves target thread using thread service.
        This handles child thread responses by finding the thread that owns the work plan.
        
        Args:
            response_thread_id: Thread ID from response (may be child thread)
            owner_uid: Owner node identifier
            
        Returns:
            WorkPlan instance for the correct thread, or None if not found
        """
        target_thread_id = self._thread_service.find_work_plan_owner(response_thread_id, owner_uid)
        if not target_thread_id:
            print(f"❌ [PLAN] Could not resolve work plan owner for thread {response_thread_id}, owner: {owner_uid}")
            return None
            
        return self.load(target_thread_id, owner_uid)
    
    def save(self, plan: WorkPlan) -> bool:
        """Save work plan to dedicated workspace field (thread-safe)."""
        with self.with_lock(plan.thread_id, plan.owner_uid):
            try:
                plan.mark_updated()
                
                workspace = self._workspace_service.get_workspace(plan.thread_id)
                workspace.context.work_plans[plan.owner_uid] = plan.model_dump()
                self._workspace_service.update_workspace(workspace)
                
                return True
            except Exception as e:
                print(f"❌ [PLAN] Save error: {e}")
                return False
    
    def get_status_summary(self, thread_id: str, owner_uid: str) -> WorkPlanStatusSummary:
        """
        Get status summary for work plan.
        
        Calculates waiting_items as IN_PROGRESS + kind=REMOTE items.
        This maintains backward compatibility while using the new status model.
        """
        plan = self.load(thread_id, owner_uid)
        
        if not plan:
            return WorkPlanStatusSummary(exists=False)
        
        counts = plan.get_status_counts()
        ready_items = plan.get_ready_items()
        
        # Check for local ready items (PENDING + LOCAL + dependencies met)
        has_local_ready = any(
            item.kind == WorkItemKind.LOCAL 
            for item in ready_items
        )
        
        # Check for remote ready items (PENDING + REMOTE + dependencies met)
        has_remote_ready = any(
            item.kind == WorkItemKind.REMOTE
            for item in ready_items
        )
        
        # Calculate remote waiting items (IN_PROGRESS + REMOTE)
        remote_in_progress_items = [
            item for item in plan.items.values()
            if item.status == WorkItemStatus.IN_PROGRESS and item.kind == WorkItemKind.REMOTE
        ]
        
        has_remote_waiting = len(remote_in_progress_items) > 0
        waiting_items_count = len(remote_in_progress_items)
        
        summary = WorkPlanStatusSummary(
            exists=True,
            total_items=len(plan.items),
            pending_items=counts.pending,
            in_progress_items=counts.in_progress,
            waiting_items=waiting_items_count,  # Calculated from IN_PROGRESS + REMOTE
            done_items=counts.done,
            failed_items=counts.failed,
            blocked_items=counts.blocked,
            has_local_ready=has_local_ready,
            has_remote_ready=has_remote_ready,
            has_remote_waiting=has_remote_waiting,
            is_complete=plan.is_complete()
        )
        
        return summary