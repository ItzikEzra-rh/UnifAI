"""
Tool for creating or updating work plans.
"""

from typing import Dict, Any, List, Optional, Callable
from pydantic import BaseModel, Field
from elements.tools.common.base_tool import BaseTool
from elements.nodes.common.workload import WorkPlan, WorkItem, WorkPlanService, WorkItemKind
from elements.nodes.common.agent.constants import ToolNames


class WorkItemSpec(BaseModel):
    """Specification for a work item to be created."""
    id: str = Field(..., description="Unique identifier for the work item (use snake_case, e.g., 'analyze_data')")
    title: str = Field(..., description="Short, descriptive title for the work item")
    description: str = Field(..., description="Detailed description of what needs to be done")
    dependencies: List[str] = Field(
        default_factory=list, 
        description="List of work item IDs that must complete before this item can start"
    )
    kind: WorkItemKind = Field(
        default=WorkItemKind.REMOTE,
        description="LOCAL for tasks you can do yourself, REMOTE for tasks to delegate to other nodes"
    )
    estimated_duration: Optional[str] = Field(
        None, 
        description="Optional time estimate (e.g., '30 minutes', '2 hours')"
    )


class CreateOrUpdatePlanArgs(BaseModel):
    """Arguments for creating or updating a work plan."""
    summary: str = Field(
        ..., 
        description="High-level summary of what this work plan accomplishes (e.g., 'Analyze Q4 sales data and create presentation')"
    )
    items: List[WorkItemSpec] = Field(
        ...,
        description="List of work items to create. Each item should have a clear purpose and dependencies.",
        min_items=1
    )


class CreateOrUpdateWorkPlanTool(BaseTool):
    """Create or update a work plan with structured work items."""
    
    name = ToolNames.WORKPLAN_CREATE_OR_UPDATE
    description = """Create a new work plan or update existing plan with structured work items.
    
    Use this to:
    - Break down complex requests into manageable work items
    - Add new work items to handle responses like "I need X and Y first"
    - Update work items based on changing requirements
    - Structure dependencies between work items
    
    WORK ITEM GUIDELINES:
    - Each item should be specific and actionable
    - Use LOCAL for tasks you can do yourself, REMOTE for delegation
    - Set dependencies by item ID (items wait for dependencies to be 'done')
    - Use snake_case for IDs (e.g., 'analyze_data', 'create_report')
    
    DEPENDENCY EXAMPLES:
    - Item 'create_report' depends on ['analyze_data', 'gather_feedback']
    - Item 'analyze_data' has no dependencies (can start immediately)
    
    WHEN TO USE:
    - Initial planning: Break down the main request
    - Response handling: Add items for "I need X first" scenarios
    - Replanning: Adjust based on new information or failures"""
    args_schema = CreateOrUpdatePlanArgs
    
    def __init__(
        self,
        get_thread_id: Callable[[], str],
        get_owner_uid: Callable[[], str],
        get_workload_service: Callable[[], Any]
    ):
        """
        Initialize with clean SOLID dependencies.
        
        Args:
            get_thread_id: Function to get current thread ID
            get_owner_uid: Function to get owner node UID
            get_workload_service: Function to get workload service
        """
        self._get_thread_id = get_thread_id
        self._get_owner_uid = get_owner_uid
        self._get_workload_service = get_workload_service
    
    def run(self, **kwargs) -> Dict[str, Any]:
        """Create or update work plan (thread-safe)."""
        print(f"📋 [DEBUG] CreateOrUpdateWorkPlanTool.run() - Starting")
        
        args = CreateOrUpdatePlanArgs(**kwargs)
        print(f"📋 [DEBUG] Plan summary: {args.summary}")
        print(f"📋 [DEBUG] Number of items: {len(args.items)}")
        
        # Get context and create domain service
        thread_id = self._get_thread_id()
        owner_uid = self._get_owner_uid()
        workload_service = self._get_workload_service()
        service = WorkPlanService(workload_service)
        
        print(f"📋 [DEBUG] Owner UID: {owner_uid}")
        
        # Thread-safe create or update operation
        with service.with_lock(thread_id, owner_uid):
            # Load existing plan or create new one
            plan = service.load(thread_id, owner_uid)
            if not plan:
                print(f"📋 [DEBUG] No existing plan - creating new one")
                plan = service.create(
                    thread_id=thread_id,
                    owner_uid=owner_uid
                )
            else:
                print(f"📋 [DEBUG] Updating existing plan with {len(plan.items)} items")
            
            # Update summary
            plan.summary = args.summary
            
            # Add items from structured specs
            for i, item_spec in enumerate(args.items):
                print(f"📋 [DEBUG] Adding item {i+1}: {item_spec.id} - {item_spec.title}")
                print(f"📋 [DEBUG] Dependencies: {item_spec.dependencies}")
                print(f"📋 [DEBUG] Kind: {item_spec.kind}")
                
                item = WorkItem(
                    id=item_spec.id,
                    title=item_spec.title,
                    description=item_spec.description,
                    dependencies=item_spec.dependencies,
                    kind=item_spec.kind
                )
                plan.items[item.id] = item
            
            print(f"📋 [DEBUG] Saving plan with {len(plan.items)} total items")
            service.save(plan)
        
        # Get status summary for response
        status_summary = service.get_status_summary(thread_id, owner_uid)
        
        result = {
            "success": True,
            "plan_id": f"{thread_id}:{owner_uid}",
            "total_items": status_summary.total_items,
            "status_counts": {
                "pending": status_summary.pending_items,
                "waiting": status_summary.waiting_items,
                "in_progress": status_summary.in_progress_items,
                "done": status_summary.done_items,
                "failed": status_summary.failed_items,
                "blocked": status_summary.blocked_items
            }
        }
        
        print(f"📋 [DEBUG] CreateOrUpdateWorkPlanTool completed: {result}")
        return result
