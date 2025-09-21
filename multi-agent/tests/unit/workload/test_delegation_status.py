"""
Unit tests for delegation status management.

Tests the new delegation status update functionality including
mark_item_as_delegated and ingest_task_response methods.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from elements.nodes.common.workload import (
    WorkPlan, WorkItem, WorkItemStatus, WorkItemKind, WorkPlanService,
    WorkItemResult, Workspace, WorkspaceContext
)


class TestDelegationStatusUpdates:
    """Test delegation status update functionality."""
    
    @pytest.fixture
    def workspace(self):
        """Create a test workspace."""
        return Workspace(
            thread_id="test-thread",
            context=WorkspaceContext()
        )
    
    @pytest.fixture
    def service(self, workspace):
        """Create WorkPlanService with test workspace."""
        return WorkPlanService(workspace)
    
    @pytest.fixture
    def sample_plan(self):
        """Create a sample work plan with items."""
        item1 = WorkItem(
            id="analyze_data",
            title="Analyze Sales Data",
            description="Extract and analyze Q4 sales metrics",
            status=WorkItemStatus.PENDING,
            kind=WorkItemKind.REMOTE
        )
        
        item2 = WorkItem(
            id="create_report",
            title="Create Report", 
            description="Generate final report",
            status=WorkItemStatus.PENDING,
            kind=WorkItemKind.LOCAL,
            dependencies=["analyze_data"]
        )
        
        plan = WorkPlan(
            summary="Q4 Analysis Project",
            owner_uid="orchestrator-1",
            thread_id="test-thread",
            items={"analyze_data": item1, "create_report": item2}
        )
        
        return plan
    
    def test_mark_item_as_delegated_success(self, service, sample_plan):
        """Test successfully marking item as delegated."""
        # Save the plan first
        service.save(sample_plan)
        
        # Mark item as delegated
        success = service.mark_item_as_delegated(
            owner_uid="orchestrator-1",
            item_id="analyze_data",
            correlation_task_id="task-123"
        )
        
        assert success is True
        
        # Verify item was updated
        updated_plan = service.load("orchestrator-1")
        updated_item = updated_plan.items["analyze_data"]
        
        assert updated_item.status == WorkItemStatus.WAITING
        assert updated_item.correlation_task_id == "task-123"
        # updated_at should be more recent
        assert updated_item.updated_at > sample_plan.items["analyze_data"].updated_at
        assert updated_plan.updated_at == updated_item.updated_at
    
    def test_mark_item_as_delegated_nonexistent_plan(self, service):
        """Test marking item as delegated when plan doesn't exist."""
        success = service.mark_item_as_delegated(
            owner_uid="nonexistent-owner",
            item_id="some-item",
            correlation_task_id="task-123"
        )
        
        assert success is False
    
    def test_mark_item_as_delegated_nonexistent_item(self, service, sample_plan):
        """Test marking nonexistent item as delegated."""
        service.save(sample_plan)
        
        success = service.mark_item_as_delegated(
            owner_uid="orchestrator-1",
            item_id="nonexistent-item",
            correlation_task_id="task-123"
        )
        
        assert success is False
    
    def test_ingest_task_response_success(self, service, sample_plan):
        """Test successfully ingesting task response."""
        # First mark item as delegated
        sample_plan.items["analyze_data"].status = WorkItemStatus.WAITING
        sample_plan.items["analyze_data"].correlation_task_id = "task-123"
        service.save(sample_plan)
        
        # Ingest successful response
        result_data = {
            "analysis": "Q4 sales increased 15%",
            "metrics": {"revenue": "$2.1M", "growth": "15%"}
        }
        
        success = service.ingest_task_response(
            owner_uid="orchestrator-1",
            correlation_task_id="task-123",
            result=result_data
        )
        
        assert success is True
        
        # Verify item was updated
        updated_plan = service.load("orchestrator-1")
        updated_item = updated_plan.items["analyze_data"]
        
        assert updated_item.status == WorkItemStatus.DONE
        assert updated_item.result_ref is not None
        assert updated_item.result_ref.success is True
        assert "Q4 sales increased 15%" in updated_item.result_ref.content
        # updated_at should be more recent
        assert updated_item.updated_at > sample_plan.items["analyze_data"].updated_at
    
    def test_ingest_task_response_error(self, service, sample_plan):
        """Test ingesting task response with error."""
        # First mark item as delegated
        sample_plan.items["analyze_data"].status = WorkItemStatus.WAITING
        sample_plan.items["analyze_data"].correlation_task_id = "task-456"
        service.save(sample_plan)
        
        # Ingest error response
        error_message = "Database connection failed after 30 seconds"
        
        success = service.ingest_task_response(
            owner_uid="orchestrator-1",
            correlation_task_id="task-456",
            error=error_message
        )
        
        assert success is True
        
        # Verify item was updated
        updated_plan = service.load("orchestrator-1")
        updated_item = updated_plan.items["analyze_data"]
        
        assert updated_item.status == WorkItemStatus.FAILED
        assert updated_item.error == error_message
        assert updated_item.result_ref is not None
        assert updated_item.result_ref.success is False
        assert updated_item.result_ref.error_details == error_message
    
    def test_ingest_task_response_nonexistent_correlation(self, service, sample_plan):
        """Test ingesting response for nonexistent correlation ID."""
        service.save(sample_plan)
        
        success = service.ingest_task_response(
            owner_uid="orchestrator-1",
            correlation_task_id="nonexistent-task",
            result="some result"
        )
        
        assert success is False
    
    def test_ingest_task_response_no_plan(self, service):
        """Test ingesting response when no plan exists."""
        success = service.ingest_task_response(
            owner_uid="nonexistent-owner",
            correlation_task_id="task-123",
            result="some result"
        )
        
        assert success is False
    
    def test_delegation_workflow_integration(self, service):
        """Test complete delegation workflow."""
        # 1. Create plan with pending item
        item = WorkItem(
            id="process_data",
            title="Process Data",
            description="Process the uploaded data",
            status=WorkItemStatus.PENDING,
            kind=WorkItemKind.REMOTE
        )
        
        plan = WorkPlan(
            summary="Data Processing Project",
            owner_uid="orchestrator-1",
            thread_id="test-thread",
            items={"process_data": item}
        )
        
        service.save(plan)
        
        # 2. Mark as delegated (simulates DelegateTaskTool)
        success = service.mark_item_as_delegated(
            owner_uid="orchestrator-1",
            item_id="process_data",
            correlation_task_id="task-789"
        )
        assert success is True
        
        # Verify status changed to WAITING
        plan = service.load("orchestrator-1")
        assert plan.items["process_data"].status == WorkItemStatus.WAITING
        assert plan.items["process_data"].correlation_task_id == "task-789"
        
        # 3. Ingest response (simulates response from remote node)
        success = service.ingest_task_response(
            owner_uid="orchestrator-1",
            correlation_task_id="task-789",
            result={"processed_records": 1000, "output_file": "processed_data.csv"}
        )
        assert success is True
        
        # Verify status changed to DONE
        plan = service.load("orchestrator-1")
        item = plan.items["process_data"]
        assert item.status == WorkItemStatus.DONE
        assert item.result_ref.success is True
        assert "processed_records" in item.result_ref.content
    
    def test_multiple_delegations_different_correlations(self, service):
        """Test multiple delegations with different correlation IDs."""
        # Create plan with multiple items
        items = {
            "task1": WorkItem(
                id="task1", title="Task 1", description="First task",
                status=WorkItemStatus.PENDING, kind=WorkItemKind.REMOTE
            ),
            "task2": WorkItem(
                id="task2", title="Task 2", description="Second task", 
                status=WorkItemStatus.PENDING, kind=WorkItemKind.REMOTE
            )
        }
        
        plan = WorkPlan(
            summary="Multi-task project",
            owner_uid="orchestrator-1", 
            thread_id="test-thread",
            items=items
        )
        
        service.save(plan)
        
        # Delegate both tasks
        service.mark_item_as_delegated("orchestrator-1", "task1", "corr-1")
        service.mark_item_as_delegated("orchestrator-1", "task2", "corr-2")
        
        # Verify both are waiting
        plan = service.load("orchestrator-1")
        assert plan.items["task1"].status == WorkItemStatus.WAITING
        assert plan.items["task2"].status == WorkItemStatus.WAITING
        assert plan.items["task1"].correlation_task_id == "corr-1"
        assert plan.items["task2"].correlation_task_id == "corr-2"
        
        # Ingest response for task1 only
        service.ingest_task_response("orchestrator-1", "corr-1", result="task1 done")
        
        # Verify only task1 is done
        plan = service.load("orchestrator-1")
        assert plan.items["task1"].status == WorkItemStatus.DONE
        assert plan.items["task2"].status == WorkItemStatus.WAITING  # Still waiting
        
        # Ingest response for task2
        service.ingest_task_response("orchestrator-1", "corr-2", error="task2 failed")
        
        # Verify task2 is failed
        plan = service.load("orchestrator-1")
        assert plan.items["task2"].status == WorkItemStatus.FAILED
    
    def test_delegation_status_affects_plan_completion(self, service):
        """Test that delegation status affects plan completion checks."""
        # Create plan with single item
        item = WorkItem(
            id="only_task",
            title="Only Task",
            description="The only task in the plan",
            status=WorkItemStatus.PENDING,
            kind=WorkItemKind.REMOTE
        )
        
        plan = WorkPlan(
            summary="Single task plan",
            owner_uid="orchestrator-1",
            thread_id="test-thread", 
            items={"only_task": item}
        )
        
        service.save(plan)
        
        # Plan should not be complete initially
        assert not plan.is_complete()
        
        # Mark as delegated - still not complete
        service.mark_item_as_delegated("orchestrator-1", "only_task", "task-123")
        plan = service.load("orchestrator-1")
        assert not plan.is_complete()
        assert plan.items["only_task"].status == WorkItemStatus.WAITING
        
        # Ingest successful response - now complete
        service.ingest_task_response("orchestrator-1", "task-123", result="success")
        plan = service.load("orchestrator-1")
        assert plan.is_complete()
        assert plan.items["only_task"].status == WorkItemStatus.DONE
    
    def test_delegation_status_affects_ready_items(self, service):
        """Test that delegation status affects ready item calculations."""
        # Create plan with dependent items
        items = {
            "first": WorkItem(
                id="first", title="First", description="First task",
                status=WorkItemStatus.PENDING, kind=WorkItemKind.REMOTE
            ),
            "second": WorkItem(
                id="second", title="Second", description="Second task",
                status=WorkItemStatus.PENDING, kind=WorkItemKind.REMOTE,
                dependencies=["first"]
            )
        }
        
        plan = WorkPlan(
            summary="Dependent tasks",
            owner_uid="orchestrator-1",
            thread_id="test-thread",
            items=items
        )
        
        service.save(plan)
        
        # Initially only first task is ready
        ready_items = plan.get_ready_items()
        assert len(ready_items) == 1
        assert ready_items[0].id == "first"
        
        # Mark first as delegated - second still not ready
        service.mark_item_as_delegated("orchestrator-1", "first", "task-123")
        plan = service.load("orchestrator-1")
        ready_items = plan.get_ready_items()
        assert len(ready_items) == 0  # first is WAITING, second is blocked
        
        # Complete first task - second becomes ready
        service.ingest_task_response("orchestrator-1", "task-123", result="first done")
        plan = service.load("orchestrator-1")
        ready_items = plan.get_ready_items()
        assert len(ready_items) == 1
        assert ready_items[0].id == "second"
    
    def test_error_handling_in_delegation_methods(self, service):
        """Test error handling in delegation methods."""
        # Test with invalid workspace state
        with patch.object(service, 'load', side_effect=Exception("Workspace error")):
            success = service.mark_item_as_delegated("owner", "item", "corr")
            assert success is False
        
        with patch.object(service, 'load', side_effect=Exception("Workspace error")):
            success = service.ingest_task_response("owner", "corr", result="data")
            assert success is False
        
        # Test with save failures
        item = WorkItem(id="test", title="Test", description="Test")
        plan = WorkPlan(
            summary="Test", owner_uid="owner", thread_id="thread",
            items={"test": item}
        )
        service.save(plan)
        
        with patch.object(service, 'save', return_value=False):
            success = service.mark_item_as_delegated("owner", "test", "corr")
            assert success is False
        
        with patch.object(service, 'save', return_value=False):
            success = service.ingest_task_response("owner", "corr", result="data")
            assert success is False


class TestDelegationStatusIntegration:
    """Test integration between delegation status and other components."""
    
    def test_delegation_with_work_plan_status_summary(self):
        """Test that delegation status is reflected in status summaries."""
        workspace = Workspace(thread_id="test", context=WorkspaceContext())
        service = WorkPlanService(workspace)
        
        # Create plan with items in various states
        items = {
            "pending": WorkItem(
                id="pending", title="Pending", description="Pending task",
                status=WorkItemStatus.PENDING
            ),
            "waiting": WorkItem(
                id="waiting", title="Waiting", description="Waiting task",
                status=WorkItemStatus.WAITING, correlation_task_id="task-1"
            ),
            "done": WorkItem(
                id="done", title="Done", description="Done task",
                status=WorkItemStatus.DONE
            )
        }
        
        plan = WorkPlan(
            summary="Mixed status plan",
            owner_uid="orchestrator-1",
            thread_id="test",
            items=items
        )
        
        service.save(plan)
        
        # Get status summary
        summary = service.get_status_summary("orchestrator-1")
        
        assert summary.exists is True
        assert summary.total_items == 3
        assert summary.pending_items == 1
        assert summary.waiting_items == 1
        assert summary.done_items == 1
        assert summary.has_remote_waiting is True  # waiting item is remote by default
        assert summary.is_complete is False
    
    def test_delegation_status_in_plan_snapshot(self):
        """Test that delegation status appears in plan snapshots."""
        # This would test the _build_plan_snapshot method in OrchestratorNode
        # but since we're testing the service layer, we verify the data is available
        
        workspace = Workspace(thread_id="test", context=WorkspaceContext())
        service = WorkPlanService(workspace)
        
        item = WorkItem(
            id="delegated_task",
            title="Delegated Task", 
            description="A task that was delegated",
            status=WorkItemStatus.WAITING,
            assigned_uid="worker_node",
            correlation_task_id="task-123"
        )
        
        plan = WorkPlan(
            summary="Delegation test",
            owner_uid="orchestrator-1",
            thread_id="test",
            items={"delegated_task": item}
        )
        
        service.save(plan)
        
        # Load and verify the data that would be used in snapshots
        loaded_plan = service.load("orchestrator-1")
        waiting_items = loaded_plan.get_items_by_status(WorkItemStatus.WAITING)
        
        assert len(waiting_items) == 1
        waiting_item = waiting_items[0]
        assert waiting_item.id == "delegated_task"
        assert waiting_item.assigned_uid == "worker_node"
        assert waiting_item.correlation_task_id == "task-123"
        
        # This data would be used to build context like:
        # "WAITING (1): - Delegated Task (ID: delegated_task) [assigned to: worker_node]"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

