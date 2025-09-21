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
    item_id: str = Field(..., description="ID of the work item")
    status: WorkItemStatus = Field(..., description="New status for the work item")
    notes: Optional[str] = Field(None, description="Additional notes about the status change")
    correlation_task_id: Optional[str] = Field(None, description="Task ID for remote delegation")


class MarkWorkItemStatusTool(BaseTool):
    """Mark the status of a work item."""
    
    name = ToolNames.WORKPLAN_MARK
    description = "Update the status of a work item (pending, in_progress, waiting, done, failed, blocked)"
    args_schema = MarkStatusArgs
    
    def __init__(
        self,
        get_workspace: Callable[[], Any],
        get_owner_uid: Callable[[], str]
    ):
        self._get_workspace = get_workspace
        self._get_owner_uid = get_owner_uid
    
    def run(self, **kwargs) -> Dict[str, Any]:
        """Mark work item status."""
        args = MarkStatusArgs(**kwargs)
        
        workspace = self._get_workspace()
        service = WorkPlanService(workspace)
        owner_uid = self._get_owner_uid()
        
        success = service.update_item_status(
            owner_uid=owner_uid,
            item_id=args.item_id,
            status=args.status,
            error=args.notes if args.status == WorkItemStatus.FAILED else None,
            correlation_task_id=args.correlation_task_id
        )
        
        if not success:
            return {"success": False, "error": "Work item not found"}
        
        return {
            "success": True,
            "item_id": args.item_id,
            "new_status": args.status.value
        }
