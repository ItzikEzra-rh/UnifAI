"""
Tool for summarizing work plans.
"""

from typing import Dict, Any, Callable
from pydantic import BaseModel
from elements.tools.common.base_tool import BaseTool
from elements.nodes.common.workload import WorkItemStatus
from elements.nodes.common.agent.constants import ToolNames


class SummarizeWorkPlanArgs(BaseModel):
    """Empty args schema (no arguments required)."""
    pass


class SummarizeWorkPlanTool(BaseTool):
    """Generate a final summary of completed work plan with results."""
    
    name = ToolNames.WORKPLAN_SUMMARIZE
    description = """Generate a comprehensive summary of the completed work plan including results and deliverables.
    
    Use this in SYNTHESIS phase to create a final report for the user. This should include
    what was accomplished, key results from each work item, and any deliverables created."""
    args_schema = SummarizeWorkPlanArgs
    
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
        """Generate summary with full structured data."""
        thread_id = self._get_thread_id()
        owner_uid = self._get_owner_uid()
        workload_service = self._get_workload_service()
        workspace_service = workload_service.get_workspace_service()
        
        plan = workspace_service.load_work_plan(thread_id, owner_uid)
        if not plan:
            return {"summary": "No work plan found", "items": []}
        
        # Build comprehensive summary with results
        lines = [
            f"Work Plan Summary: {plan.summary}",
            f"Total Items: {len(plan.items)}",
            f"Status: {plan.get_status_counts().model_dump()}"
        ]
        
        # ✅ NEW: Collect structured item data for LLM
        items_data = []
        
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
                
                # ✅ Add structured data
                items_data.append({
                    "id": item.id,
                    "title": item.title,
                    "status": item.status.value,
                    "assigned_to": item.assigned_uid,  # 🎯 Agent/node UID shown here
                    "result": {
                        "content": item.result_ref.content if item.result_ref else None,
                        "data": item.result_ref.data if item.result_ref else None,
                        "success": item.result_ref.success if item.result_ref else None,
                        "metadata": item.result_ref.metadata if item.result_ref else None
                    } if item.result_ref else None
                })
        
        # Add WAITING items with responses (pending interpretation)
        waiting_items = plan.get_items_by_status(WorkItemStatus.WAITING)
        if waiting_items:
            # Check if any have responses
            waiting_with_responses = [item for item in waiting_items if item.result_ref]
            if waiting_with_responses:
                lines.append(f"\nWaiting for Interpretation ({len(waiting_with_responses)}):")
                for item in waiting_with_responses:
                    lines.append(f"  ⏳ {item.title}")
                    if item.result_ref and item.result_ref.content:
                        lines.append(f"     Response: {item.result_ref.content[:100]}...")
                    if item.assigned_uid:
                        lines.append(f"     From: {item.assigned_uid}")
                    
                    # ✅ Add structured data (this is critical for LLM interpretation!)
                    items_data.append({
                        "id": item.id,
                        "title": item.title,
                        "status": item.status.value,
                        "assigned_to": item.assigned_uid,  # 🎯 Agent/node UID shown here
                        "result": {
                            "content": item.result_ref.content,
                            "data": item.result_ref.data,
                            "success": item.result_ref.success,
                            "metadata": item.result_ref.metadata
                        }
                    })
        
        # Add failed items with errors
        failed_items = plan.get_items_by_status(WorkItemStatus.FAILED)
        if failed_items:
            lines.append(f"\nFailed Work ({len(failed_items)}):")
            for item in failed_items:
                lines.append(f"  ❌ {item.title}")
                if item.error:
                    lines.append(f"     Error: {item.error}")
                
                # ✅ Add structured data
                items_data.append({
                    "id": item.id,
                    "title": item.title,
                    "status": item.status.value,
                    "assigned_to": item.assigned_uid,  # 🎯 Agent/node UID shown here
                    "error": item.error
                })
        
        # Add any incomplete items
        incomplete_statuses = [WorkItemStatus.PENDING, WorkItemStatus.IN_PROGRESS]
        incomplete_items = []
        for status in incomplete_statuses:
            incomplete_items.extend(plan.get_items_by_status(status))
        
        if incomplete_items:
            lines.append(f"\nIncomplete Work ({len(incomplete_items)}):")
            for item in incomplete_items:
                lines.append(f"  ⏳ {item.title} ({item.status.value})")
                
                # ✅ Add structured data  
                items_data.append({
                    "id": item.id,
                    "title": item.title,
                    "status": item.status.value,
                    "assigned_to": item.assigned_uid  # 🎯 Agent/node UID shown here
                })
        
        # ✅ Return BOTH text summary AND structured data
        return {
            "summary": "\n".join(lines),
            "items": items_data  # LLM can now access all AgentResult fields!
        }
