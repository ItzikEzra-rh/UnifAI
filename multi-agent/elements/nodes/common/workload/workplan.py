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


class ResponseRecord(BaseModel):
    """
    Single response in a multi-turn conversation with a work item.
    
    Tracks one response from a delegated agent, including timing, source,
    and structured data. Used for re-delegation and iterative refinement.
    
    Note: Thread workspace contains full conversation context. This record
    is primarily for structured storage and analytics.
    """
    from_uid: str = Field(..., description="UID of the agent that responded")
    content: str = Field(..., description="Response content/message")
    data: Optional[Dict[str, Any]] = Field(None, description="Structured response data (AgentResult, etc.)")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="When response was received")
    sequence: int = Field(..., description="Order in conversation (0-indexed)")
    correlation_task_id: Optional[str] = Field(None, description="Task ID for this specific delegation")


class WorkItemResult(BaseModel):
    """
    Complete result of work item execution, including conversation history.
    
    Supports multi-turn conversations when orchestrator re-delegates or asks follow-ups.
    The 'responses' list preserves full conversation history for structured access.
    
    Design Note: Thread workspace contains conversation context for agents.
    This model stores structured history for orchestrator analytics and LLM reasoning.
    """
    # Final result (set by LLM via MarkWorkItemStatusTool)
    success: bool = Field(default=False, description="Final success status (set when marked DONE)")
    content: Optional[str] = Field(None, description="Final synthesized result or summary")
    data: Optional[Dict[str, Any]] = Field(None, description="Final structured result data")
    
    # Conversation history (for re-delegation and follow-ups)
    responses: List[ResponseRecord] = Field(
        default_factory=list, 
        description="All responses received, in chronological order. Supports multi-turn conversations."
    )
    
    # Metadata
    artifacts: List[str] = Field(default_factory=list, description="List of created artifacts")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Processing metadata")
    
    @property
    def has_responses(self) -> bool:
        """Check if any responses have been received."""
        return len(self.responses) > 0
    
    @property
    def latest_response(self) -> Optional[ResponseRecord]:
        """Get the most recent response."""
        return self.responses[-1] if self.responses else None
    
    @property
    def response_count(self) -> int:
        """Get total number of responses received."""
        return len(self.responses)
    
    def get_conversation_summary(self, max_turns: int = 5) -> str:
        """
        Get a formatted summary of the conversation.
        
        Args:
            max_turns: Maximum number of recent turns to include
            
        Returns:
            Formatted conversation summary
        """
        if not self.responses:
            return "No responses yet"
        
        recent = self.responses[-max_turns:] if len(self.responses) > max_turns else self.responses
        lines = [f"Conversation ({len(self.responses)} turn{'s' if len(self.responses) > 1 else ''}):"]
        
        for resp in recent:
            preview = resp.content[:80] + "..." if len(resp.content) > 80 else resp.content
            lines.append(f"  [{resp.sequence}] {resp.from_uid}: {preview}")
        
        if len(self.responses) > max_turns:
            lines.insert(1, f"  ... ({len(self.responses) - max_turns} earlier turns)")
        
        return "\n".join(lines)
    
    @property
    def content_with_history(self) -> str:
        """
        Get content including response history for backward compatibility.
        
        If no final content is set, returns latest response or conversation summary.
        This ensures old code that reads result_ref.content still works.
        """
        if self.content:
            return self.content
        
        if not self.responses:
            return ""
        
        # Return latest response for single turn
        if len(self.responses) == 1:
            return self.responses[0].content
        
        # Synthesize from multiple responses
        return "\n\n---\n\n".join([
            f"[Turn {resp.sequence}] {resp.from_uid}:\n{resp.content}"
            for resp in self.responses
        ])


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
    result_ref: Optional[WorkItemResult] = Field(None, description="Execution result")
    error: Optional[str] = Field(None, description="Error message if failed")
    correlation_task_id: Optional[str] = Field(None, description="Task ID for delegation tracking")
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
    has_remote_waiting: bool = False  # True if any IN_PROGRESS + kind=REMOTE items exist
    has_responses: bool = False  # True if any IN_PROGRESS + kind=REMOTE items have result_ref
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
    
    def atomic_update_item(
        self, 
        thread_id: str, 
        owner_uid: str, 
        item_id: str, 
        update_func: callable
    ) -> bool:
        """
        Atomically update a work item using the provided function.
        
        Args:
            thread_id: Thread identifier
            owner_uid: Owner node identifier
            item_id: Work item identifier
            update_func: Function that takes (item, plan) and modifies the item
            
        Returns:
            True if update succeeded, False otherwise
        """
        with self.with_lock(thread_id, owner_uid):
            plan = self.load(thread_id, owner_uid)
            if not plan or item_id not in plan.items:
                return False
            
            item = plan.items[item_id]
            update_func(item, plan)
            item.mark_updated()
            return self.save(plan)
    
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
        
        # Check for local ready items
        has_local_ready = any(
            item.kind == WorkItemKind.LOCAL 
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
            has_remote_waiting=has_remote_waiting,
            is_complete=plan.is_complete()
        )
        
        return summary
    
    def store_task_response(
        self,
        thread_id: str,
        owner_uid: str,
        correlation_task_id: str,
        response_content: str,
        from_uid: str
    ) -> bool:
        """Store task response as context without changing status - let LLM interpret."""
        
        plan = self.load(thread_id, owner_uid)
        if not plan:
            return False
        
        # Find item by correlation task ID
        target_item = None
        for item in plan.items.values():
            if item.correlation_task_id == correlation_task_id:
                target_item = item
                break
        
        if not target_item:
            return False
        
        
        # Store response content without changing status
        if not target_item.result_ref:
            target_item.result_ref = WorkItemResult(
                success=False,  # Not finalized yet
                content=response_content,
                metadata={"from_uid": from_uid, "needs_interpretation": True}
            )
        else:
            # Append to existing content
            target_item.result_ref.content += f"\n\n--- Response from {from_uid} ---\n{response_content}"
            if target_item.result_ref.metadata:
                target_item.result_ref.metadata["needs_interpretation"] = True
            else:
                target_item.result_ref.metadata = {"from_uid": from_uid, "needs_interpretation": True}
        
        target_item.mark_updated()
        self.save(plan)
        return True

    def ingest_task_response(
        self, 
        thread_id: str,
        owner_uid: str, 
        correlation_task_id: str, 
        result: Any = None, 
        error: str = None
    ) -> bool:
        """Ingest task response and update work item status - only for explicit success/error (thread-safe)."""
        
        with self.with_lock(thread_id, owner_uid):
            plan = self.load(thread_id, owner_uid)
            if not plan:
                return False
            
            # Find item by correlation task ID
            target_item = None
            for item in plan.items.values():
                if item.correlation_task_id == correlation_task_id:
                    target_item = item
                    break
            
            if not target_item:
                return False
            
            
            # Update item based on response - only for explicit structures
            if error:
                target_item.status = WorkItemStatus.FAILED
                target_item.error = error
                target_item.retry_count += 1  # Increment retry count on failure
            elif result and isinstance(result, dict) and result.get("success") is True:
                # Only auto-mark DONE for explicit success structures
                target_item.status = WorkItemStatus.DONE
                target_item.result_ref = WorkItemResult(
                    success=True,
                    content=str(result.get("content", result)),
                    data=result
                )
            else:
                return False  # Don't auto-mark, let LLM interpret
            
            target_item.mark_updated()
            self.save(plan)
            return True
    
    def update_item_status(
        self,
        thread_id: str,
        owner_uid: str,
        item_id: str,
        status: WorkItemStatus,
        error: str = None,
        correlation_task_id: str = None
    ) -> bool:
        """Update work item status - for LLM-driven status changes (thread-safe)."""
        
        with self.with_lock(thread_id, owner_uid):
            plan = self.load(thread_id, owner_uid)
            if not plan:
                return False
            
            item = plan.items.get(item_id)
            if not item:
                return False
            
            
            old_status = item.status
            item.status = status
            
            if error and status == WorkItemStatus.FAILED:
                item.error = error
            
            if correlation_task_id:
                item.correlation_task_id = correlation_task_id
            
            # If marking as DONE, finalize the result
            if status == WorkItemStatus.DONE and item.result_ref:
                item.result_ref.success = True
                if item.result_ref.metadata:
                    item.result_ref.metadata.pop("needs_interpretation", None)
            
            item.mark_updated()
            self.save(plan)
            return True
    
    def mark_item_as_delegated(self, thread_id: str, owner_uid: str, item_id: str, correlation_task_id: str) -> bool:
        """Mark work item as delegated (WAITING status) - thread-safe."""
        
        with self.with_lock(thread_id, owner_uid):
            plan = self.load(thread_id, owner_uid)
            if not plan:
                return False
            
            item = plan.items.get(item_id)
            if not item:
                return False
            
            
            item.status = WorkItemStatus.WAITING
            item.correlation_task_id = correlation_task_id
            item.mark_updated()
            
            self.save(plan)
            return True
    
    # ========== WORKSPACE WORK PLAN ACCESS ==========
    
    def get_work_plans(self, thread_id: str) -> Dict[str, Dict[str, Any]]:
        """Get all work plans in workspace."""
        workspace = self._workspace_service.get_workspace(thread_id)
        return workspace.context.work_plans.copy()
    
    def remove_work_plan(self, thread_id: str, owner_uid: str) -> None:
        """Remove work plan for specific owner."""
        workspace = self._workspace_service.get_workspace(thread_id)
        if owner_uid in workspace.context.work_plans:
            del workspace.context.work_plans[owner_uid]
            self._workspace_service.update_workspace(workspace)
    
    def work_plan_exists(self, thread_id: str, owner_uid: str) -> bool:
        """Check if work plan exists for specific owner."""
        workspace = self._workspace_service.get_workspace(thread_id)
        return owner_uid in workspace.context.work_plans