"""
Tool for marking work item status.
"""

from typing import Dict, Any, Optional, Callable
from pydantic import BaseModel, Field
from elements.tools.common.base_tool import BaseTool
from elements.nodes.common.workload import WorkItemStatus, WorkItemKind
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
        - 'in_progress': Task is actively being worked on (local execution or remote delegation)
        - 'pending': Task is ready to start but not yet begun
        
        Note: For delegated items waiting for responses, they're automatically marked as 'in_progress'.
        Use this tool primarily to mark items as 'done' or 'failed' after reviewing responses."""
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
    description = """FINAL STATUS DECISION - Use this to mark work item status ONLY when you're certain.

    When to use this tool:
    - 'done': Work is COMPLETE, quality is acceptable, all requirements met
    - 'failed': Work CANNOT be completed (retries exhausted, fundamentally impossible)
    - 'in_progress': Starting local execution
    - 'pending': Reset for re-assignment
    
    ⚠️ IMPORTANT - DON'T RUSH TO MARK 'DONE':
    - If response is incomplete → Use DelegateTaskTool to ask for more
    - If response is unclear → Use DelegateTaskTool to ask for clarification
    - If response is partial → Use DelegateTaskTool to request the rest
    - Only mark 'done' when you're truly satisfied with the result
    
    REMEMBER: Thread context is preserved - you can re-delegate multiple times to get quality results.
    Better to ask follow-up questions than accept incomplete work!"""
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
        """Mark work item status (thread-safe)."""
        args = MarkStatusArgs(**kwargs)
        
        thread_id = self._get_thread_id()
        owner_uid = self._get_owner_uid()
        workload_service = self._get_workload_service()
        workspace_service = workload_service.get_workspace_service()
        
        # VALIDATION: Prevent marking DONE if waiting for delegation response
        if args.status == WorkItemStatus.DONE:
            # Load the work item to check state
            plan = workspace_service.load_work_plan(thread_id, owner_uid)
            if not plan or args.item_id not in plan.items:
                return {"success": False, "error": "Work item not found"}
            
            item = plan.items[args.item_id]
            
            # Check if item is actively delegated (IN_PROGRESS + REMOTE + has correlation_task_id)
            if (item.status == WorkItemStatus.IN_PROGRESS and 
                item.kind == WorkItemKind.REMOTE and 
                item.correlation_task_id):
                
                # Check if we have a response for the CURRENT active delegation
                has_response_for_current_task = False
                if item.result_ref and item.result_ref.responses:
                    has_response_for_current_task = any(
                        r.correlation_task_id == item.correlation_task_id
                        for r in item.result_ref.responses
                    )
                
                if not has_response_for_current_task:
                    return {
                        "success": False,
                        "error": f"Cannot mark '{args.item_id}' as DONE - still waiting for response from delegated agent (task {item.correlation_task_id[:8]}...). Wait for response to arrive, or use status='failed' to give up and move on."
                    }
        
        def update_status(item, plan):
            """Update function for atomic status change."""
            item.status = args.status
            if args.status == WorkItemStatus.FAILED and args.notes:
                item.error = args.notes
            if args.correlation_task_id:
                item.correlation_task_id = args.correlation_task_id
            
            # Mark all responses as processed when changing status (LLM has acted by marking status)
            if item.result_ref and item.result_ref.responses:
                for response in item.result_ref.responses:
                    response.processed = True
        
        success = workspace_service.atomic_update_work_item(thread_id, owner_uid, args.item_id, update_status)
        
        if not success:
            return {"success": False, "error": "Work plan or work item not found"}
        
        result = {
            "success": True,
            "item_id": args.item_id,
            "new_status": args.status.value
        }
        return result
