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
    """Status of a work item."""
    PENDING = "pending"
    WAITING = "waiting"
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


class WorkItemResult(BaseModel):
    """Result of work item execution."""
    success: bool = Field(default=True, description="Whether the work item succeeded")
    content: Optional[str] = Field(None, description="Result content or summary")
    data: Optional[Dict[str, Any]] = Field(None, description="Structured result data")
    artifacts: List[str] = Field(default_factory=list, description="List of created artifacts")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Processing metadata (from_uid, needs_interpretation, etc.)")


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
    """Count of work items by status."""
    pending: int = 0
    waiting: int = 0
    in_progress: int = 0
    done: int = 0
    failed: int = 0
    blocked: int = 0
    
    @property
    def total(self) -> int:
        """Total count of all items."""
        return self.pending + self.waiting + self.in_progress + self.done + self.failed + self.blocked


class WorkPlanStatusSummary(BaseModel):
    """Summary of work plan status."""
    exists: bool = False
    total_items: int = 0
    pending_items: int = 0
    in_progress_items: int = 0
    waiting_items: int = 0
    done_items: int = 0
    failed_items: int = 0
    blocked_items: int = 0
    has_local_ready: bool = False
    has_remote_waiting: bool = False
    has_responses: bool = False
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
        """Get IDs of completed items (DONE or FAILED)."""
        completed = set()
        for item_id, item in self.items.items():
            if item.status in [WorkItemStatus.DONE, WorkItemStatus.FAILED]:
                completed.add(item_id)
        return completed
    
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
    
    def get_items_by_status(self, status: WorkItemStatus) -> List[WorkItem]:
        """Get all items with the specified status."""
        return [item for item in self.items.values() if item.status == status]
    
    def get_status_counts(self) -> WorkItemStatusCounts:
        """Get count of items by status."""
        counts = WorkItemStatusCounts()
        completed_ids = self.get_completed_item_ids()
        
        for item in self.items.values():
            if item.status == WorkItemStatus.PENDING:
                if item.is_blocked(completed_ids):
                    counts.blocked += 1
                else:
                    counts.pending += 1
            elif item.status == WorkItemStatus.WAITING:
                counts.waiting += 1
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
                print(f"💾 [PLAN] Loaded: {len(plan.items)} items")
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
                
                print(f"💾 [PLAN] Saved: {len(plan.items)} items")
                return True
            except Exception as e:
                print(f"❌ [PLAN] Save error: {e}")
                return False
    
    def get_status_summary(self, thread_id: str, owner_uid: str) -> WorkPlanStatusSummary:
        """Get status summary for work plan."""
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
        
        # Check for remote waiting items
        has_remote_waiting = any(
            item.status == WorkItemStatus.WAITING and item.kind == WorkItemKind.REMOTE
            for item in plan.items.values()
        )
        
        summary = WorkPlanStatusSummary(
            exists=True,
            total_items=len(plan.items),
            pending_items=counts.pending,
            in_progress_items=counts.in_progress,
            waiting_items=counts.waiting,
            done_items=counts.done,
            failed_items=counts.failed,
            blocked_items=counts.blocked,
            has_local_ready=has_local_ready,
            has_remote_waiting=has_remote_waiting,
            is_complete=plan.is_complete()
        )
        
        print(f"📊 [DEBUG] Returning status summary: {summary.model_dump()}")
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
        print(f"💬 [DEBUG] WorkPlanService.store_task_response() - Storing response for LLM interpretation")
        print(f"💬 [DEBUG] correlation_task_id: {correlation_task_id}, from: {from_uid}")
        
        plan = self.load(thread_id, owner_uid)
        if not plan:
            print(f"❌ [DEBUG] No plan found for {owner_uid}")
            return False
        
        # Find item by correlation task ID
        target_item = None
        for item in plan.items.values():
            if item.correlation_task_id == correlation_task_id:
                target_item = item
                break
        
        if not target_item:
            print(f"❌ [DEBUG] No work item found for correlation task ID: {correlation_task_id}")
            return False
        
        print(f"💬 [DEBUG] Found target item: {target_item.id} - {target_item.title}")
        
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
        print(f"💬 [DEBUG] Response stored for LLM interpretation")
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
        print(f"📥 [DEBUG] WorkPlanService.ingest_task_response() - Processing response")
        print(f"📥 [DEBUG] correlation_task_id: {correlation_task_id}")
        print(f"📥 [DEBUG] has_result: {result is not None}, has_error: {error is not None}")
        
        with self.with_lock(thread_id, owner_uid):
            plan = self.load(thread_id, owner_uid)
            if not plan:
                print(f"❌ [DEBUG] No plan found for {owner_uid}")
                return False
            
            # Find item by correlation task ID
            target_item = None
            for item in plan.items.values():
                if item.correlation_task_id == correlation_task_id:
                    target_item = item
                    break
            
            if not target_item:
                print(f"❌ [DEBUG] No work item found for correlation task ID: {correlation_task_id}")
                print(f"📋 [DEBUG] Available correlation IDs: {[item.correlation_task_id for item in plan.items.values() if item.correlation_task_id]}")
                return False
            
            print(f"✅ [DEBUG] Found target item: {target_item.id} - {target_item.title}")
            
            # Update item based on response - only for explicit structures
            if error:
                print(f"❌ [DEBUG] Marking item as FAILED: {error}")
                target_item.status = WorkItemStatus.FAILED
                target_item.error = error
                target_item.retry_count += 1  # Increment retry count on failure
            elif result and isinstance(result, dict) and result.get("success") is True:
                # Only auto-mark DONE for explicit success structures
                print(f"✅ [DEBUG] Marking item as DONE with explicit success result")
                target_item.status = WorkItemStatus.DONE
                target_item.result_ref = WorkItemResult(
                    success=True,
                    content=str(result.get("content", result)),
                    data=result
                )
            else:
                print(f"💬 [DEBUG] Result is not explicit success structure - not auto-marking DONE")
                return False  # Don't auto-mark, let LLM interpret
            
            target_item.mark_updated()
            self.save(plan)
            print(f"✅ [DEBUG] Task response ingested successfully")
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
        print(f"🔄 [DEBUG] WorkPlanService.update_item_status() - Updating {item_id} to {status}")
        
        with self.with_lock(thread_id, owner_uid):
            plan = self.load(thread_id, owner_uid)
            if not plan:
                print(f"❌ [DEBUG] No plan found for {owner_uid}")
                return False
            
            item = plan.items.get(item_id)
            if not item:
                print(f"❌ [DEBUG] No item found with ID: {item_id}")
                print(f"📋 [DEBUG] Available item IDs: {list(plan.items.keys())}")
                return False
            
            print(f"✅ [DEBUG] Found item: {item.title}")
            print(f"🔄 [DEBUG] Changing status: {item.status} → {status}")
            
            old_status = item.status
            item.status = status
            
            if error and status == WorkItemStatus.FAILED:
                item.error = error
                print(f"❌ [DEBUG] Added error message: {error}")
            
            if correlation_task_id:
                item.correlation_task_id = correlation_task_id
                print(f"🔗 [DEBUG] Set correlation_task_id: {correlation_task_id}")
            
            # If marking as DONE, finalize the result
            if status == WorkItemStatus.DONE and item.result_ref:
                item.result_ref.success = True
                if item.result_ref.metadata:
                    item.result_ref.metadata.pop("needs_interpretation", None)
                print(f"✅ [DEBUG] Finalized result as successful")
            
            item.mark_updated()
            self.save(plan)
            print(f"✅ [DEBUG] Item status updated: {old_status} → {status}")
            return True
    
    def mark_item_as_delegated(self, thread_id: str, owner_uid: str, item_id: str, correlation_task_id: str) -> bool:
        """Mark work item as delegated (WAITING status) - thread-safe."""
        print(f"📤 [DEBUG] WorkPlanService.mark_item_as_delegated() - Marking {item_id} as delegated")
        print(f"📤 [DEBUG] correlation_task_id: {correlation_task_id}")
        
        with self.with_lock(thread_id, owner_uid):
            plan = self.load(thread_id, owner_uid)
            if not plan:
                print(f"❌ [DEBUG] No plan found for {owner_uid}")
                return False
            
            item = plan.items.get(item_id)
            if not item:
                print(f"❌ [DEBUG] No item found with ID: {item_id}")
                print(f"📋 [DEBUG] Available item IDs: {list(plan.items.keys())}")
                return False
            
            print(f"✅ [DEBUG] Found item: {item.title}")
            print(f"🔄 [DEBUG] Changing status: {item.status} → WAITING")
            
            item.status = WorkItemStatus.WAITING
            item.correlation_task_id = correlation_task_id
            item.mark_updated()
            
            self.save(plan)
            print(f"✅ [DEBUG] Item marked as delegated successfully")
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