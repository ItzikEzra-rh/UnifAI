"""
Workload Management Module

SOLID design for thread and workspace management in the multi-agent system.
Provides focused interfaces and implementations for workload orchestration.
"""

# Core models
from .models import AgentResult
from .task import Task
from .context import WorkspaceContext
from .thread import Thread, ThreadStatus
from .workspace import Workspace, ArtifactRef
from .agent_thread import AgentThread

# Work plan components (WorkPlanService is deprecated - use WorkspaceService instead)
from .workplan import (
    WorkPlan, WorkItem, WorkItemStatus, WorkItemKind,
    ToolArguments, WorkItemResult, WorkItemStatusCounts, WorkPlanStatusSummary,
    LocalExecution, DelegationExchange
)

# New SOLID services
from .thread_service import IThreadService, ThreadService
from .workspace_service import IWorkspaceService, WorkspaceService
from .storage import IWorkloadStorage, InMemoryStorage, StateBoundStorage
from .unified_service import IWorkloadService, UnifiedWorkloadService

# Legacy components can be imported from storage and unified_service if needed

__all__ = [
    # Core models
    'AgentResult',
    'WorkspaceContext', 
    'Task',
    'Thread',
    'ThreadStatus',
    'Workspace',
    'ArtifactRef',
    'AgentThread',
    
    # Work plan components (WorkPlanService removed - use WorkspaceService.load_work_plan() instead)
    'WorkPlan',
    'WorkItem',
    'WorkItemStatus',
    'WorkItemKind',
    'ToolArguments',
    'WorkItemResult',
    'WorkItemStatusCounts',
    'WorkPlanStatusSummary',
    'LocalExecution',
    'DelegationExchange',
    
    # New SOLID services
    'IThreadService',
    'ThreadService',
    'IWorkspaceService', 
    'WorkspaceService',
    'IWorkloadStorage',
    'InMemoryStorage',
    'StateBoundStorage',
    'IWorkloadService',
    'UnifiedWorkloadService',
    
]