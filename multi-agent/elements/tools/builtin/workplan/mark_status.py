"""
Tool for marking work item status.
"""

from typing import Dict, Any, Optional, Callable
from pydantic import BaseModel, Field
from elements.tools.common.base_tool import BaseTool
from elements.nodes.common.workload import WorkItemStatus, WorkPlanService
from elements.nodes.common.agent.constants import ToolNames


class MarkStatusArgs(BaseModel):
    """Arguments for marking work item status."""
    item_id: str = Field(
        ..., 
        description="ID of the work item to update (get from work plan context)"
    )
    status: WorkItemStatus = Field(
        ..., 
        description="""New status for the work item. Valid values:
        - 'done': Task completed successfully (use when you've confirmed the work is finished)
        - 'failed': Task failed and cannot be completed (use when errors are unrecoverable)
        - 'in_progress': Task is actively being worked on
        - 'blocked': Task cannot proceed due to dependencies or external factors
        - 'pending': Task is ready to start but not yet begun
        - 'waiting': Task is delegated and waiting for response"""
    )
    notes: Optional[str] = Field(
        None, 
        description="Detailed explanation of why you're changing the status. REQUIRED for 'failed' status to explain what went wrong and retry history. Helpful for 'done' to summarize what was accomplished."
    )
    correlation_task_id: Optional[str] = Field(
        None, 
        description="Only needed if this status change relates to a specific delegated task ID"
    )


class MarkWorkItemStatusTool(BaseTool):
    """Finalize work item status after interpreting responses or completing work."""
    
    name = ToolNames.WORKPLAN_MARK
    description = """Update work item status based on your interpretation of responses or completion of work.

    Use this tool to:
    - Mark items 'done' when you've confirmed successful completion
    - Mark items 'failed' when they cannot be completed (with explanation in notes)
    - Mark items 'blocked' when waiting for external dependencies
    - Update status during work progression
    
    IMPORTANT: Only mark 'done' when you're confident the work is actually complete.
    For ambiguous responses, consider asking for clarification first."""
    args_schema = MarkStatusArgs
    
    def __init__(
        self,
        get_thread_id: Callable[[], str],
        get_owner_uid: Callable[[], str],
        get_workload_service: Callable[[], Any]
    ):
        self._get_thread_id = get_thread_id
        self._get_owner_uid = get_owner_uid
        self._get_workload_service = get_workload_service
    
    def run(self, **kwargs) -> Dict[str, Any]:
        """Mark work item status."""
        print(f"🏷️ [DEBUG] MarkWorkItemStatusTool.run() - Starting")
        args = MarkStatusArgs(**kwargs)
        print(f"🏷️ [DEBUG] Item ID: {args.item_id}")
        print(f"🏷️ [DEBUG] New status: {args.status}")
        print(f"🏷️ [DEBUG] Notes: {args.notes}")
        
        thread_id = self._get_thread_id()
        owner_uid = self._get_owner_uid()
        workload_service = self._get_workload_service()
        service = WorkPlanService(workload_service)
        print(f"🏷️ [DEBUG] Owner UID: {owner_uid}")
        
        # Load plan, update item, and save
        plan = service.load(thread_id, owner_uid)
        if not plan or args.item_id not in plan.items:
            print(f"❌ [DEBUG] Work plan or item not found")
            return {"success": False, "error": "Work plan or work item not found"}
        
        # Update the item status
        item = plan.items[args.item_id]
        item.status = args.status
        if args.status == WorkItemStatus.FAILED and args.notes:
            item.error = args.notes
        if args.correlation_task_id:
            item.correlation_task_id = args.correlation_task_id
        
        # Save the updated plan
        success = service.save(plan)
        
        if not success:
            print(f"❌ [DEBUG] Failed to save updated work plan")
            return {"success": False, "error": "Failed to save work plan"}
        
        result = {
            "success": True,
            "item_id": args.item_id,
            "new_status": args.status.value
        }
        print(f"✅ [DEBUG] MarkWorkItemStatusTool completed: {result}")
        return result
