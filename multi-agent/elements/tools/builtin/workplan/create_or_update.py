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
        get_workspace: Callable[[], Any],
        get_thread_id: Callable[[], str],
        get_owner_uid: Callable[[], str]
    ):
        """
        Initialize with workspace accessors.
        
        Args:
            get_workspace: Function to get current workspace
            get_thread_id: Function to get current thread ID
            get_owner_uid: Function to get owner node UID
        """
        self._get_workspace = get_workspace
        self._get_thread_id = get_thread_id
        self._get_owner_uid = get_owner_uid
    
    def run(self, **kwargs) -> Dict[str, Any]:
        """Create or update work plan."""
        print(f"📋 [DEBUG] CreateOrUpdateWorkPlanTool.run() - Starting")
        
        args = CreateOrUpdatePlanArgs(**kwargs)
        print(f"📋 [DEBUG] Plan summary: {args.summary}")
        print(f"📋 [DEBUG] Number of items: {len(args.items)}")
        
        workspace = self._get_workspace()
        service = WorkPlanService(workspace)
        owner_uid = self._get_owner_uid()
        
        print(f"📋 [DEBUG] Owner UID: {owner_uid}")
        
        # Load existing plan or create new one
        plan = service.load(owner_uid)
        if not plan:
            print(f"📋 [DEBUG] No existing plan - creating new one")
            plan = service.create(
                thread_id=self._get_thread_id(),
                owner_uid=owner_uid,
                created_by=owner_uid
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
        
        result = {
            "success": True,
            "plan_id": f"{plan.thread_id}:{plan.owner_uid}",
            "total_items": len(plan.items),
            "status_counts": plan.get_status_counts().model_dump()
        }
        
        print(f"📋 [DEBUG] CreateOrUpdateWorkPlanTool completed: {result}")
        return result
