"""
Tool for delegating tasks to other nodes.
"""

from typing import Dict, Any, Callable, Optional
from pydantic import BaseModel, Field
from elements.tools.common.base_tool import BaseTool
from elements.nodes.common.workload import Task, WorkItemStatus
from elements.nodes.common.agent.constants import ToolNames


class DelegateTaskArgs(BaseModel):
    """Simplified arguments for delegating a task to an adjacent node."""
    dst_uid: str = Field(
        ..., 
        description="UID of the target adjacent node (check with ListAdjacentNodesTool first)"
    )
    content: str = Field(
        ...,
        description="Clear, detailed description of what the target node should do. Include context and expected deliverables."
    )
    work_item_id: str = Field(
        ...,
        description="ID of the work item being delegated (required for proper status tracking and response correlation)"
    )
    data: Dict[str, Any] = Field(
        default_factory=dict, 
        description="Additional structured data the target node might need"
    )


class DelegateTaskTool(BaseTool):
    """Delegate a task to an adjacent node via IEM."""
    
    name = ToolNames.IEM_DELEGATE_TASK
    description = """Delegate a task to an adjacent node with automatic thread and status management.
    
    Use this to:
    - Send work items to specialized nodes (work_item_id required for status tracking)
    - Coordinate distributed work execution across the orchestration network
    - Enable proper response correlation and dependency resolution
    
    WORKFLOW:
    1. Use ListAdjacentNodesTool to find capable nodes
    2. Use GetNodeCardTool to understand their capabilities  
    3. Use this tool to delegate with clear, specific instructions
    4. Child thread created automatically for delegation context
    5. Work item status automatically updates to 'waiting'
    6. Prevents circular delegation in hierarchical orchestration
    
    IMPORTANT: 
    - Be specific in 'content' - include context, requirements, and expected deliverables
    - Always provide work_item_id to ensure proper orchestration workflow
    - This tool is designed for structured orchestration, not ad-hoc communication"""
    args_schema = DelegateTaskArgs
    
    def __init__(
        self,
        send_task: Callable[[str, Task], str],
        get_owner_uid: Callable[[], str],
        get_current_thread: Callable[[], Any],  # Returns Thread object
        get_thread_service: Callable[[], Any],
        get_workspace_service: Callable[[], Any],
        check_adjacency: Optional[Callable[[str], bool]] = None
    ):
        """
        Initialize with focused service dependencies.
        
        Args:
            send_task: Function to send task via IEM (dst_uid, task) -> packet_id
            get_owner_uid: Function to get current node UID
            get_current_thread: Function to get current Thread object
            get_thread_service: Function to get thread service
            get_workspace_service: Function to get workspace service
            check_adjacency: Optional function to verify adjacency
        """
        self._send_task = send_task
        self._get_owner_uid = get_owner_uid
        self._get_current_thread = get_current_thread
        self._get_thread_service = get_thread_service
        self._get_workspace_service = get_workspace_service
        self._check_adjacency = check_adjacency
    
    def run(self, **kwargs) -> Dict[str, Any]:
        """Delegate task to adjacent node with automatic thread and status management."""
        print(f"📤 [DEBUG] DelegateTaskTool.run() - Starting delegation")
        
        args = DelegateTaskArgs(**kwargs)
        print(f"📤 [DEBUG] Target: {args.dst_uid}")
        print(f"📤 [DEBUG] Content: {args.content[:100]}...")
        print(f"📤 [DEBUG] Work item ID: {args.work_item_id}")
        
        # Get current thread context
        current_thread = self._get_current_thread()
        print(f"📤 [DEBUG] Current thread: {current_thread.thread_id}")
        
        # Check adjacency if validator provided
        if self._check_adjacency and not self._check_adjacency(args.dst_uid):
            error_msg = f"Node {args.dst_uid} is not adjacent, or the uid is wrong, check what it is really adjacent"
            print(f"❌ [DEBUG] Adjacency check failed: {error_msg}")
            return {
                "success": False,
                "error": error_msg
            }
        
        # Prevent circular delegation
        if self._would_create_cycle(args.dst_uid, current_thread):
            error_msg = f"Circular delegation detected: {args.dst_uid} is already in delegation chain"
            print(f"❌ [DEBUG] Circular delegation prevented: {error_msg}")
            return {
                "success": False,
                "error": error_msg
            }
        
        print(f"✅ [DEBUG] Adjacency check passed")
        
        # Use provided work_item_id (now required)
        work_item_id = args.work_item_id
        print(f"📝 [DEBUG] Work item ID: {work_item_id}")
        
        # Create child thread for delegation
        print(f"📝 [DEBUG] Creating child thread for delegation")
        child_thread = current_thread.create_child(
            title=f"Delegated: {args.content[:50]}...",
            objective=args.content,
            initiator=self._get_owner_uid()
        )
        print(f"📝 [DEBUG] Created child thread: {child_thread.thread_id}")
        
        # Create task with child thread context
        print(f"📝 [DEBUG] Creating task for delegation")
        task = Task.create(
            content=args.content,
            data=args.data,
            should_respond=True,  # Always request response for delegation
            thread_id=child_thread.thread_id,
            created_by=self._get_owner_uid()
        )
        
        print(f"📝 [DEBUG] Created task with ID: {task.task_id}")
        
        # Add work item reference (always present now)
        task.data["work_item_id"] = work_item_id
        print(f"📝 [DEBUG] Added work_item_id to task data")
        
        # Set response destination
        task.response_to = self._get_owner_uid()
        print(f"📝 [DEBUG] Set response destination to: {task.response_to}")
        
        try:
            # Send via IEM
            print(f"📡 [DEBUG] Sending task via IEM to {args.dst_uid}")
            packet_id = self._send_task(args.dst_uid, task)
            print(f"📡 [DEBUG] Task sent successfully, packet ID: {packet_id}")
            
            # Save threads (parent and child)
            print(f"💾 [DEBUG] Saving threads")
            thread_service = self._get_thread_service()
            thread_service.save_thread(current_thread)  # Parent thread with updated children
            thread_service.save_thread(child_thread)    # New child thread
            print(f"✅ [DEBUG] Threads saved successfully")
            
            # Update work item status to WAITING (always done now)
            print(f"🔄 [DEBUG] Updating work item status to WAITING and assigning to {args.dst_uid}")
            try:
                owner_uid = self._get_owner_uid()
                workspace_service = self._get_workspace_service()
                
                # Mark item as delegated with correlation task ID and assigned UID
                success = workspace_service.mark_work_item_as_delegated(
                    current_thread.thread_id, 
                    owner_uid, 
                    work_item_id, 
                    task.task_id,
                    args.dst_uid  # ✅ Pass the assigned node UID
                )
                
                if not success:
                    error_msg = f"Work item {work_item_id} not found in work plan"
                    print(f"❌ [DEBUG] {error_msg}")
                    return {
                        "success": False,
                        "error": error_msg
                    }
                
                print(f"✅ [DEBUG] Work item status updated and assigned to {args.dst_uid}")
            except Exception as e:
                error_msg = f"Exception updating work item status: {e}"
                print(f"❌ [DEBUG] {error_msg}")
                return {
                    "success": False,
                    "error": error_msg
                }
            
            result = {
                "success": True,
                "task_id": task.task_id,
                "packet_id": packet_id,
                "dst_uid": args.dst_uid,
                "child_thread_id": child_thread.thread_id,
                "parent_thread_id": current_thread.thread_id,
                "correlation_info": {
                    "task_id": task.task_id,
                    "work_item_id": work_item_id,
                    "child_thread_id": child_thread.thread_id
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
    
    # ========== HELPER METHODS ==========
    
    def _would_create_cycle(self, dst_uid: str, current_thread) -> bool:
        """
        Check if delegation would create a cycle using thread service.
        
        Args:
            dst_uid: Target node UID for delegation
            current_thread: Current thread context
            
        Returns:
            True if delegation would create a cycle
        """
        try:
            thread_service = self._get_thread_service()
            return thread_service.detect_delegation_cycle(current_thread.thread_id, dst_uid)
        except Exception as e:
            print(f"⚠️ [DEBUG] Error checking delegation cycle: {e}")
            return False  # Allow delegation if we can't check
    
