"""
Tool for delegating tasks to other nodes.
"""

from typing import Dict, Any, Callable, Optional
from pydantic import BaseModel, Field
from elements.tools.common.base_tool import BaseTool
from elements.nodes.common.workload import Task, WorkPlanService
from elements.nodes.common.agent.constants import ToolNames


class DelegateTaskArgs(BaseModel):
    """Arguments for delegating a task to an adjacent node."""
    dst_uid: str = Field(
        ..., 
        description="UID of the target adjacent node (check with ListAdjacentNodesTool first)"
    )
    content: str = Field(
        ..., 
        description="Clear, detailed description of what the target node should do. Include context and expected deliverables."
    )
    thread_id: str = Field(..., description="Current thread ID for maintaining context")
    parent_item_id: Optional[str] = Field(
        None, 
        description="ID of the work item being delegated (required to track status updates)"
    )
    should_respond: bool = Field(
        True, 
        description="Whether to request a response (almost always True for orchestration)"
    )
    data: Dict[str, Any] = Field(
        default_factory=dict, 
        description="Additional structured data the target node might need"
    )


class DelegateTaskTool(BaseTool):
    """Delegate a task to an adjacent node via IEM."""
    
    name = ToolNames.IEM_DELEGATE_TASK
    description = """Send a task to an adjacent node for remote execution.
    
    Use this when a work item needs capabilities that an adjacent node has.
    Always provide the parent_item_id to link delegation with work plan tracking.
    The target node will work on the task and send results back automatically."""
    args_schema = DelegateTaskArgs
    
    def __init__(
        self,
        send_task: Callable[[str, Task], str],
        get_owner_uid: Callable[[], str],
        get_workspace: Callable[[], Any],
        check_adjacency: Optional[Callable[[str], bool]] = None
    ):
        """
        Initialize with IEM task sender.
        
        Args:
            send_task: Function to send task via IEM (dst_uid, task) -> packet_id
            get_owner_uid: Function to get current node UID
            get_workspace: Function to get workspace for status updates
            check_adjacency: Optional function to verify adjacency
        """
        self._send_task = send_task
        self._get_owner_uid = get_owner_uid
        self._get_workspace = get_workspace
        self._check_adjacency = check_adjacency
    
    def run(self, **kwargs) -> Dict[str, Any]:
        """Delegate task to adjacent node."""
        print(f"📤 [DEBUG] DelegateTaskTool.run() - Starting delegation")
        
        args = DelegateTaskArgs(**kwargs)
        print(f"📤 [DEBUG] Target: {args.dst_uid}")
        print(f"📤 [DEBUG] Content: {args.content[:100]}...")
        print(f"📤 [DEBUG] Parent item ID: {args.parent_item_id}")
        print(f"📤 [DEBUG] Should respond: {args.should_respond}")
        
        # Check adjacency if validator provided
        if self._check_adjacency and not self._check_adjacency(args.dst_uid):
            error_msg = f"Node {args.dst_uid} is not adjacent, or the uid is wrong, check what it is really adjacent"
            print(f"❌ [DEBUG] Adjacency check failed: {error_msg}")
            return {
                "success": False,
                "error": error_msg
            }
        
        print(f"✅ [DEBUG] Adjacency check passed")
        
        # Create task
        print(f"📝 [DEBUG] Creating task for delegation")
        task = Task.create(
            content=args.content,
            data=args.data,
            should_respond=args.should_respond,
            thread_id=args.thread_id,
            created_by=self._get_owner_uid()
        )
        
        print(f"📝 [DEBUG] Created task with ID: {task.task_id}")
        
        # Add parent reference if provided
        if args.parent_item_id:
            task.data["parent_item_id"] = args.parent_item_id
            print(f"📝 [DEBUG] Added parent_item_id to task data")
        
        # Set response destination
        if args.should_respond:
            task.response_to = self._get_owner_uid()
            print(f"📝 [DEBUG] Set response destination to: {task.response_to}")
        
        try:
            # Send via IEM
            print(f"📡 [DEBUG] Sending task via IEM to {args.dst_uid}")
            packet_id = self._send_task(args.dst_uid, task)
            print(f"📡 [DEBUG] Task sent successfully, packet ID: {packet_id}")
            
            # Update work item status to WAITING if parent_item_id provided
            if args.parent_item_id:
                print(f"🔄 [DEBUG] Updating work item status to WAITING")
                try:
                    workspace = self._get_workspace()
                    service = WorkPlanService(workspace)
                    success = service.mark_item_as_delegated(
                        owner_uid=self._get_owner_uid(),
                        item_id=args.parent_item_id,
                        correlation_task_id=task.task_id
                    )
                    if success:
                        print(f"✅ [DEBUG] Work item status updated successfully")
                    else:
                        print(f"⚠️ [DEBUG] Failed to update work item status")
                except Exception as e:
                    print(f"❌ [DEBUG] Exception updating work item status: {e}")
            
            result = {
                "success": True,
                "task_id": task.task_id,
                "packet_id": packet_id,
                "dst_uid": args.dst_uid,
                "correlation_info": {
                    "task_id": task.task_id,
                    "parent_item_id": args.parent_item_id
                }
            }
            
            print(f"✅ [DEBUG] DelegateTaskTool completed successfully: {result}")
            return result
            
        except Exception as e:
            error_msg = f"Failed to send task: {str(e)}"
            print(f"❌ [DEBUG] Delegation failed: {error_msg}")
            return {
                "success": False,
                "error": error_msg
            }
