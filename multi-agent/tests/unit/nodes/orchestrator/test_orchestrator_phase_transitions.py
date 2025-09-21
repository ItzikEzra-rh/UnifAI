"""
Unit tests for orchestrator phase transitions.

Tests the OrchestratorPhaseContextProvider and OrchestratorPhaseTransitionPolicy
for correct mapping from service summary to WorkPlanStatus and phase decisions.
"""

import pytest
from unittest.mock import Mock, MagicMock

from elements.nodes.orchestrator.orchestrator_node import (
    OrchestratorPhaseContextProvider, OrchestratorPhaseTransitionPolicy
)
from elements.nodes.common.agent.phase_protocols import create_work_plan_status, create_phase_state
from elements.nodes.common.agent.constants import ExecutionPhase
from elements.nodes.common.workload import WorkPlanService, Workspace


class TestOrchestratorPhaseContextProvider:
    """Test OrchestratorPhaseContextProvider mapping correctness."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_node = Mock()
        self.mock_node.uid = "orchestrator-123"
        self.thread_id = "thread-456"
        
        self.provider = OrchestratorPhaseContextProvider(self.mock_node, self.thread_id)
    
    def test_empty_plan_mapping(self):
        """Test mapping when no plan exists."""
        # Mock workspace and service
        mock_workspace = Mock(spec=Workspace)
        self.mock_node.get_workspace.return_value = mock_workspace
        
        # Mock service returning no plan
        with pytest.MonkeyPatch().context() as m:
            mock_service = Mock(spec=WorkPlanService)
            from elements.nodes.common.workload import WorkPlanStatusSummary
            mock_service.get_status_summary.return_value = WorkPlanStatusSummary(
                exists=False, total_items=0, is_complete=False, has_local_ready=False, has_remote_waiting=False,
                pending_items=0, in_progress_items=0, waiting_items=0, done_items=0, failed_items=0, blocked_items=0
            )
            m.setattr("elements.nodes.orchestrator.orchestrator_node.WorkPlanService", 
                     lambda workspace: mock_service)
            
            context = self.provider.get_phase_context()
        
        # Should return empty work plan status
        assert context.work_plan_status is not None
        assert context.work_plan_status.total_items == 0
        assert context.work_plan_status.is_complete is False
        assert context.thread_id == self.thread_id
        assert context.node_uid == "orchestrator-123"
    
    def test_non_existent_plan_mapping(self):
        """Test mapping when plan doesn't exist."""
        mock_workspace = Mock(spec=Workspace)
        self.mock_node.get_workspace.return_value = mock_workspace
        
        with pytest.MonkeyPatch().context() as m:
            mock_service = Mock(spec=WorkPlanService)
            from elements.nodes.common.workload import WorkPlanStatusSummary
            mock_service.get_status_summary.return_value = WorkPlanStatusSummary(
                exists=False, total_items=0, is_complete=False, has_local_ready=False, has_remote_waiting=False,
                pending_items=0, in_progress_items=0, waiting_items=0, done_items=0, failed_items=0, blocked_items=0
            )
            m.setattr("elements.nodes.orchestrator.orchestrator_node.WorkPlanService", 
                     lambda workspace: mock_service)
            
            context = self.provider.get_phase_context()
        
        # Should return empty work plan status
        assert context.work_plan_status.total_items == 0
        assert context.work_plan_status.is_complete is False
    
    def test_active_plan_mapping(self):
        """Test mapping of active plan with various statuses."""
        mock_workspace = Mock(spec=Workspace)
        self.mock_node.get_workspace.return_value = mock_workspace
        
        # Mock service response with active plan
        with pytest.MonkeyPatch().context() as m:
            mock_service = Mock(spec=WorkPlanService)
            from elements.nodes.common.workload import WorkPlanStatusSummary, WorkItemStatusCounts
            mock_service.get_status_summary.return_value = WorkPlanStatusSummary(
                exists=True,
                total_items=5,
                status_counts=WorkItemStatusCounts(
                    pending=1, in_progress=2, waiting=1, done=1, failed=0, blocked=0
                ),
                has_local_ready=True,
                has_remote_waiting=True,
                is_complete=False,
                pending_items=1,
                in_progress_items=2,
                waiting_items=1,
                done_items=1,
                failed_items=0,
                blocked_items=0
            )
            m.setattr("elements.nodes.orchestrator.orchestrator_node.WorkPlanService", 
                     lambda workspace: mock_service)
            
            context = self.provider.get_phase_context()
        
        # Should correctly map all fields
        status = context.work_plan_status
        assert status.total_items == 5
        assert status.pending_items == 1
        assert status.in_progress_items == 2
        assert status.waiting_items == 1
        assert status.done_items == 1
        assert status.failed_items == 0
        assert status.blocked_items == 0
        assert status.has_local_ready is True
        assert status.has_remote_waiting is True
        assert status.is_complete is False
    
    def test_completed_plan_mapping(self):
        """Test mapping of completed plan."""
        mock_workspace = Mock(spec=Workspace)
        self.mock_node.get_workspace.return_value = mock_workspace
        
        service_response = {
            "exists": True,
            "total_items": 3,
            "status_counts": {
                "pending": 0,
                "in_progress": 0,
                "waiting": 0,
                "done": 3,
                "failed": 0,
                "blocked": 0
            },
            "has_local_ready": False,
            "has_remote_waiting": False,
            "is_complete": True
        }
        
        with pytest.MonkeyPatch().context() as m:
            mock_service = Mock(spec=WorkPlanService)
            mock_service.get_status_summary.return_value = service_response
            m.setattr("elements.nodes.orchestrator.orchestrator_node.WorkPlanService", 
                     lambda workspace: mock_service)
            
            context = self.provider.get_phase_context()
        
        status = context.work_plan_status
        assert status.total_items == 3
        assert status.done_items == 3
        assert status.is_complete is True
        assert status.has_local_ready is False
        assert status.has_remote_waiting is False
    
    def test_error_handling(self):
        """Test error handling when service fails."""
        # Mock node to raise exception
        self.mock_node.get_workspace.side_effect = Exception("Workspace error")
        
        context = self.provider.get_phase_context()
        
        # Should return empty state on error
        assert context.work_plan_status.total_items == 0
        assert context.thread_id == self.thread_id
        assert context.node_uid == "orchestrator-123"


class TestOrchestratorPhaseTransitionPolicy:
    """Test OrchestratorPhaseTransitionPolicy phase decisions."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.policy = OrchestratorPhaseTransitionPolicy()
    
    def test_empty_plan_goes_to_planning(self):
        """Test that empty plan transitions to planning."""
        state = create_phase_state(
            work_plan_status=create_work_plan_status(total_items=0)
        )
        
        phase = self.policy.decide(
            state=state,
            current=ExecutionPhase.MONITORING,
            observations=[]
        )
        
        assert phase == ExecutionPhase.PLANNING
    
    def test_no_plan_goes_to_planning(self):
        """Test that no plan transitions to planning."""
        state = create_phase_state(work_plan_status=None)
        
        phase = self.policy.decide(
            state=state,
            current=ExecutionPhase.ALLOCATION,
            observations=[]
        )
        
        assert phase == ExecutionPhase.PLANNING
    
    def test_completed_plan_goes_to_synthesis(self):
        """Test that completed plan transitions to synthesis."""
        state = create_phase_state(
            work_plan_status=create_work_plan_status(
                total_items=3,
                done_items=3,
                is_complete=True
            )
        )
        
        phase = self.policy.decide(
            state=state,
            current=ExecutionPhase.MONITORING,
            observations=[]
        )
        
        assert phase == ExecutionPhase.SYNTHESIS
    
    def test_pending_items_go_to_allocation(self):
        """Test that pending items transition to allocation."""
        state = create_phase_state(
            work_plan_status=create_work_plan_status(
                total_items=5,
                pending_items=2,
                in_progress_items=1,
                done_items=2
            )
        )
        
        phase = self.policy.decide(
            state=state,
            current=ExecutionPhase.PLANNING,
            observations=[]
        )
        
        assert phase == ExecutionPhase.ALLOCATION
    
    def test_local_ready_goes_to_execution(self):
        """Test that local ready items transition to execution."""
        state = create_phase_state(
            work_plan_status=create_work_plan_status(
                total_items=3,
                pending_items=0,
                has_local_ready=True
            )
        )
        
        phase = self.policy.decide(
            state=state,
            current=ExecutionPhase.ALLOCATION,
            observations=[]
        )
        
        assert phase == ExecutionPhase.EXECUTION
    
    def test_in_progress_goes_to_monitoring(self):
        """Test that in-progress items transition to monitoring."""
        state = create_phase_state(
            work_plan_status=create_work_plan_status(
                total_items=3,
                pending_items=0,
                in_progress_items=2,
                has_local_ready=False
            )
        )
        
        phase = self.policy.decide(
            state=state,
            current=ExecutionPhase.EXECUTION,
            observations=[]
        )
        
        assert phase == ExecutionPhase.MONITORING
    
    def test_waiting_items_go_to_monitoring(self):
        """Test that waiting items transition to monitoring."""
        state = create_phase_state(
            work_plan_status=create_work_plan_status(
                total_items=3,
                pending_items=0,
                waiting_items=2,
                has_local_ready=False
            )
        )
        
        phase = self.policy.decide(
            state=state,
            current=ExecutionPhase.ALLOCATION,
            observations=[]
        )
        
        assert phase == ExecutionPhase.MONITORING
    
    def test_remote_waiting_goes_to_monitoring(self):
        """Test that remote waiting items transition to monitoring."""
        state = create_phase_state(
            work_plan_status=create_work_plan_status(
                total_items=3,
                pending_items=0,
                has_local_ready=False,
                has_remote_waiting=True
            )
        )
        
        phase = self.policy.decide(
            state=state,
            current=ExecutionPhase.ALLOCATION,
            observations=[]
        )
        
        assert phase == ExecutionPhase.MONITORING
    
    def test_unclear_state_defaults_to_monitoring(self):
        """Test that unclear state defaults to monitoring."""
        state = create_phase_state(
            work_plan_status=create_work_plan_status(
                total_items=3,
                pending_items=0,
                has_local_ready=False,
                has_remote_waiting=False,
                in_progress_items=0,
                waiting_items=0
            )
        )
        
        phase = self.policy.decide(
            state=state,
            current=ExecutionPhase.EXECUTION,
            observations=[]
        )
        
        assert phase == ExecutionPhase.MONITORING
    
    def test_phase_priority_order(self):
        """Test that phase decisions follow correct priority order."""
        # Completed takes priority over everything
        state = create_phase_state(
            work_plan_status=create_work_plan_status(
                total_items=3,
                pending_items=1,  # Would normally go to allocation
                is_complete=True  # But this takes priority
            )
        )
        
        phase = self.policy.decide(
            state=state,
            current=ExecutionPhase.ALLOCATION,
            observations=[]
        )
        
        assert phase == ExecutionPhase.SYNTHESIS
        
        # Pending takes priority over local ready
        state = create_phase_state(
            work_plan_status=create_work_plan_status(
                total_items=3,
                pending_items=1,      # This takes priority
                has_local_ready=True  # Over this
            )
        )
        
        phase = self.policy.decide(
            state=state,
            current=ExecutionPhase.PLANNING,
            observations=[]
        )
        
        assert phase == ExecutionPhase.ALLOCATION

