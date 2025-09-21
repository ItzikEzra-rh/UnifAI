"""
Tool for summarizing work plans.
"""

from typing import Dict, Any, Callable
from pydantic import BaseModel
from elements.tools.common.base_tool import BaseTool
from elements.nodes.common.workload import WorkPlanService, WorkItemStatus
from elements.nodes.common.agent.constants import ToolNames


class SummarizeWorkPlanTool(BaseTool):
    """Generate a final summary of completed work plan with results."""
    
    name = ToolNames.WORKPLAN_SUMMARIZE
    description = """Generate a comprehensive summary of the completed work plan including results and deliverables.
    
    Use this in SYNTHESIS phase to create a final report for the user. This should include
    what was accomplished, key results from each work item, and any deliverables created."""
    args_schema = BaseModel  # No arguments
    
    def __init__(
        self,
        get_workspace: Callable[[], Any],
        get_owner_uid: Callable[[], str]
    ):
        self._get_workspace = get_workspace
        self._get_owner_uid = get_owner_uid
    
    def run(self, **kwargs) -> Dict[str, Any]:
        """Generate summary."""
        workspace = self._get_workspace()
        service = WorkPlanService(workspace)
        owner_uid = self._get_owner_uid()
        
        plan = service.load(owner_uid)
        if not plan:
            return {"summary": "No work plan found"}
        
        # Build comprehensive summary with results
        lines = [
            f"Work Plan Summary: {plan.summary}",
            f"Total Items: {len(plan.items)}",
            f"Status: {plan.get_status_counts().model_dump()}"
        ]
        
        # Add completed items with results
        completed_items = plan.get_items_by_status(WorkItemStatus.DONE)
        if completed_items:
            lines.append(f"\nCompleted Work ({len(completed_items)}):")
            for item in completed_items:
                lines.append(f"  ✅ {item.title}")
                if item.result_ref and item.result_ref.content:
                    lines.append(f"     Result: {item.result_ref.content[:100]}...")
                if item.assigned_uid:
                    lines.append(f"     Completed by: {item.assigned_uid}")
        
        # Add failed items with errors
        failed_items = plan.get_items_by_status(WorkItemStatus.FAILED)
        if failed_items:
            lines.append(f"\nFailed Work ({len(failed_items)}):")
            for item in failed_items:
                lines.append(f"  ❌ {item.title}")
                if item.error:
                    lines.append(f"     Error: {item.error}")
        
        # Add any incomplete items
        incomplete_statuses = [WorkItemStatus.PENDING, WorkItemStatus.WAITING, WorkItemStatus.IN_PROGRESS]
        incomplete_items = []
        for status in incomplete_statuses:
            incomplete_items.extend(plan.get_items_by_status(status))
        
        if incomplete_items:
            lines.append(f"\nIncomplete Work ({len(incomplete_items)}):")
            for item in incomplete_items:
                lines.append(f"  ⏳ {item.title} ({item.status.value})")
        
        return {"summary": "\n".join(lines)}
