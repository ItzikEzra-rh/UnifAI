"""
Tool for assigning work items to execution targets.
"""

from typing import Dict, Any, Optional, Callable
from pydantic import BaseModel, Field
from elements.tools.common.base_tool import BaseTool
from elements.nodes.common.workload import WorkPlanService, WorkItemKind
from elements.nodes.common.agent.constants import ToolNames


class AssignItemArgs(BaseModel):
    """Arguments for assigning a work item."""
    item_id: str = Field(..., description="ID of the work item to assign")
    kind: WorkItemKind = Field(..., description="Kind of assignment: local or remote")
    assigned_uid: Optional[str] = Field(None, description="UID of target node (required for remote)")
    tool: Optional[str] = Field(None, description="Tool name for local execution")
    args: Dict[str, Any] = Field(default_factory=dict, description="Arguments for tool execution")


class AssignWorkItemTool(BaseTool):
    """Assign a work item to local or remote execution."""
    
    name = ToolNames.WORKPLAN_ASSIGN
    description = "Assign a work item to local execution (with a tool) or remote execution (to an adjacent node)"
    args_schema = AssignItemArgs
    
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
        """Assign work item."""
        args = AssignItemArgs(**kwargs)
        
        thread_id = self._get_thread_id()
        owner_uid = self._get_owner_uid()
        workload_service = self._get_workload_service()
        service = WorkPlanService(workload_service)
        
        plan = service.load(thread_id, owner_uid)
        if not plan:
            return {"success": False, "error": "No work plan found"}
        
        if args.item_id not in plan.items:
            return {"success": False, "error": f"Work item {args.item_id} not found"}
        
        item = plan.items[args.item_id]
        item.kind = args.kind
        item.assigned_uid = args.assigned_uid
        item.tool = args.tool
        item.args = args.args
        item.updated_at = plan.updated_at
        
        service.save(plan)
        
        return {
            "success": True,
            "item_id": args.item_id,
            "assignment": {
                "kind": args.kind,
                "assigned_uid": args.assigned_uid,
                "tool": args.tool
            }
        }
