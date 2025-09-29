"""
WorkloadCapableMixin for clean workload service access.

SOLID design providing focused service access without 250+ helper methods.
Uses new unified service architecture.
"""

from typing import ClassVar
from graph.state.graph_state import Channel
from ..workload.unified_service import IWorkloadService, UnifiedWorkloadService
from ..workload.thread_service import IThreadService
from ..workload.workspace_service import IWorkspaceService
from ..workload.thread import Thread


class WorkloadCapableMixin:
    """
    Simplified mixin providing clean service access.
    
    SOLID SRP: Only service access, not hundreds of helper methods.
    Focuses on composition and delegation to specialized services.
    """

    # Channel permissions for workload management
    MIXIN_READS: ClassVar[set[str]] = {Channel.THREADS, Channel.WORKSPACES, Channel.TASK_THREADS}
    MIXIN_WRITES: ClassVar[set[str]] = {Channel.THREADS, Channel.WORKSPACES, Channel.TASK_THREADS}

    def __init__(self, **kwargs):
        """Initialize mixin and call super() for proper MRO."""
        super().__init__(**kwargs)

    def get_workload_service(self) -> IWorkloadService:
        """
        Get unified workload service bound to current state.
        
        Returns:
            IWorkloadService instance providing access to all workload services
        """
        state = self.get_state()
        return UnifiedWorkloadService.create_state_bound(state)

    # ========== SERVICE ACCESS PROPERTIES ==========
    
    @property
    def threads(self) -> IThreadService:
        """Access thread service."""
        return self.get_workload_service().get_thread_service()
    
    @property  
    def workspaces(self) -> IWorkspaceService:
        """Access workspace service (includes work plan operations)."""
        return self.get_workload_service().get_workspace_service()
    
    # ========== COMMON OPERATIONS (Optional convenience) ==========
    
    def create_child_thread(self, parent: Thread, title: str, objective: str) -> Thread:
        """Convenience: Create child thread."""
        return self.threads.create_child_thread(parent, title, objective, self.uid)
    
    def add_fact_to_workspace(self, thread_id: str, fact: str) -> None:
        """Convenience: Add fact to workspace."""
        self.workspaces.add_fact(thread_id, fact)
    
    def set_workspace_variable(self, thread_id: str, key: str, value) -> None:
        """Convenience: Set workspace variable."""
        self.workspaces.set_variable(thread_id, key, value)
    
    def get_workspace_variable(self, thread_id: str, key: str, default=None):
        """Convenience: Get workspace variable."""
        return self.workspaces.get_variable(thread_id, key, default)
    
    # ========== GRAPHSTATE INTEGRATION HELPER ==========
    
    def copy_graphstate_messages_to_workspace(self, thread_id: str, limit: int = 10, strategy: str = "conversation") -> int:
        """
        Copy recent GraphState messages to workspace.
        
        Clean delegation to workspace service with proper GraphState access.
        Replaces the old scattered _copy_graphstate_messages_to_workspace implementations.
        
        Args:
            thread_id: Target workspace thread
            limit: Maximum number of recent messages to copy
            strategy: Sync strategy - "conversation" (default), "facts", or "both"
            
        Returns:
            Number of messages copied
        """
        try:
            # Get GraphState messages using proper access pattern
            state = self.get_state()
            from graph.state.graph_state import Channel
            graphstate_messages = state.get(Channel.MESSAGES, [])
            
            # Delegate to workspace service (SOLID delegation)
            synced_count = self.workspaces.sync_from_graphstate(
                thread_id, graphstate_messages, limit, strategy
            )
            
            if synced_count > 0:
                print(f"📝 [DEBUG] Synced {synced_count} messages from GraphState to workspace")
            
            return synced_count
                
        except Exception as e:
            print(f"⚠️ [DEBUG] Error syncing GraphState messages: {e}")
            return 0