"""
Unit tests for Pydantic WorkPlan and WorkItem models.

Tests the new Pydantic-based models for validation, serialization,
dependencies, and all new functionality added.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from elements.nodes.common.workload import (
    WorkPlan, WorkItem, WorkItemStatus, WorkItemKind, WorkPlanService,
    ToolArguments, WorkItemResult, WorkItemStatusCounts, WorkPlanStatusSummary
)


class TestWorkItemPydantic:
    """Test Pydantic WorkItem model."""
    
    def test_create_work_item_minimal(self):
        """Test creating work item with minimal required fields."""
        item = WorkItem(
            id="test_item",
            title="Test Task",
            description="A test work item"
        )
        
        assert item.id == "test_item"
        assert item.title == "Test Task"
        assert item.description == "A test work item"
        assert item.status == WorkItemStatus.PENDING
        assert item.kind == WorkItemKind.LOCAL  # Default
        assert item.dependencies == []
        assert item.args.model_dump() == {}  # Default empty ToolArguments
        assert item.result_ref is None
        assert item.error is None
        assert item.assigned_uid is None
        assert item.tool is None
        assert item.correlation_task_id is None
        assert isinstance(item.created_at, str)
        assert isinstance(item.updated_at, str)
    
    def test_create_work_item_full(self):
        """Test creating work item with all fields."""
        args = ToolArguments(query="test", limit=10)
        result = WorkItemResult(
            success=True,
            content="Task completed",
            artifacts=["file1.txt", "file2.txt"],
            metadata={"duration": "5min"}
        )
        
        item = WorkItem(
            id="full_item",
            title="Full Task",
            description="A complete work item",
            dependencies=["dep1", "dep2"],
            status=WorkItemStatus.IN_PROGRESS,
            kind=WorkItemKind.REMOTE,
            assigned_uid="worker_node",
            tool="data_processor",
            args=args,
            result_ref=result,
            error=None,
            correlation_task_id="task_123"
        )
        
        assert item.id == "full_item"
        assert item.dependencies == ["dep1", "dep2"]
        assert item.status == WorkItemStatus.IN_PROGRESS
        assert item.kind == WorkItemKind.REMOTE
        assert item.assigned_uid == "worker_node"
        assert item.tool == "data_processor"
        assert item.args.query == "test"
        assert item.args.limit == 10
        assert item.result_ref.success is True
        assert item.result_ref.content == "Task completed"
        assert item.result_ref.artifacts == ["file1.txt", "file2.txt"]
        assert item.correlation_task_id == "task_123"
    
    def test_work_item_validation(self):
        """Test Pydantic validation."""
        # Missing required fields should fail
        with pytest.raises(ValidationError):
            WorkItem()  # Missing id, title, description
        
        with pytest.raises(ValidationError):
            WorkItem(id="test")  # Missing title, description
        
        # Invalid enum values should fail
        with pytest.raises(ValidationError):
            WorkItem(
                id="test", title="Test", description="Test",
                status="invalid_status"
            )
        
        with pytest.raises(ValidationError):
            WorkItem(
                id="test", title="Test", description="Test",
                kind="invalid_kind"
            )
    
    def test_work_item_dependencies_logic(self):
        """Test dependency checking logic."""
        # Item with no dependencies is always ready
        item1 = WorkItem(id="item1", title="Task 1", description="First task")
        assert item1.is_ready_for_execution(set())
        assert item1.is_ready_for_execution({"other_item"})
        assert not item1.is_blocked(set())
        
        # Item with dependencies
        item2 = WorkItem(
            id="item2", title="Task 2", description="Second task",
            dependencies=["item1", "item3"]
        )
        
        # Not ready if dependencies not complete
        assert not item2.is_ready_for_execution(set())
        assert not item2.is_ready_for_execution({"item1"})  # Missing item3
        assert item2.is_blocked(set())
        assert item2.is_blocked({"item1"})
        
        # Ready if all dependencies complete
        assert item2.is_ready_for_execution({"item1", "item3"})
        assert item2.is_ready_for_execution({"item1", "item3", "extra"})
        assert not item2.is_blocked({"item1", "item3"})
    
    def test_work_item_serialization(self):
        """Test Pydantic serialization/deserialization."""
        original = WorkItem(
            id="serialize_test",
            title="Serialize Test",
            description="Test serialization",
            dependencies=["dep1"],
            kind=WorkItemKind.REMOTE,
            args=ToolArguments(param1="value1", param2=42)
        )
        
        # Serialize to dict
        data = original.model_dump()
        assert data["id"] == "serialize_test"
        assert data["title"] == "Serialize Test"
        assert data["dependencies"] == ["dep1"]
        assert data["kind"] == "remote"
        assert data["args"]["param1"] == "value1"
        assert data["args"]["param2"] == 42
        
        # Deserialize from dict
        restored = WorkItem(**data)
        assert restored.id == original.id
        assert restored.title == original.title
        assert restored.dependencies == original.dependencies
        assert restored.kind == original.kind
        assert restored.args.param1 == original.args.param1
        assert restored.args.param2 == original.args.param2


class TestWorkPlanPydantic:
    """Test Pydantic WorkPlan model."""
    
    def test_create_work_plan(self):
        """Test creating work plan."""
        plan = WorkPlan(
            summary="Test plan",
            owner_uid="orchestrator_1",
            thread_id="thread_123"
        )
        
        assert plan.summary == "Test plan"
        assert plan.owner_uid == "orchestrator_1"
        assert plan.thread_id == "thread_123"
        assert plan.items == {}
        assert isinstance(plan.created_at, str)
        assert isinstance(plan.updated_at, str)
    
    def test_work_plan_with_items(self):
        """Test work plan with work items."""
        item1 = WorkItem(id="item1", title="Task 1", description="First task")
        item2 = WorkItem(id="item2", title="Task 2", description="Second task", dependencies=["item1"])
        
        plan = WorkPlan(
            summary="Multi-item plan",
            owner_uid="orchestrator_1",
            thread_id="thread_123",
            items={"item1": item1, "item2": item2}
        )
        
        assert len(plan.items) == 2
        assert "item1" in plan.items
        assert "item2" in plan.items
        assert plan.items["item1"].title == "Task 1"
        assert plan.items["item2"].dependencies == ["item1"]
    
    def test_get_completed_item_ids(self):
        """Test getting completed item IDs."""
        item1 = WorkItem(id="item1", title="Task 1", description="Done", status=WorkItemStatus.DONE)
        item2 = WorkItem(id="item2", title="Task 2", description="Failed", status=WorkItemStatus.FAILED)
        item3 = WorkItem(id="item3", title="Task 3", description="Pending", status=WorkItemStatus.PENDING)
        
        plan = WorkPlan(
            summary="Test",
            owner_uid="test",
            thread_id="test",
            items={"item1": item1, "item2": item2, "item3": item3}
        )
        
        completed = plan.get_completed_item_ids()
        assert completed == {"item1", "item2"}  # Both DONE and FAILED count as completed
    
    def test_get_ready_items(self):
        """Test getting ready items based on dependencies."""
        item1 = WorkItem(id="item1", title="Task 1", description="Ready")
        item2 = WorkItem(id="item2", title="Task 2", description="Blocked", dependencies=["item1"])
        item3 = WorkItem(id="item3", title="Task 3", description="Also ready")
        item4 = WorkItem(id="item4", title="Task 4", description="Multi-dep", dependencies=["item1", "item3"])
        
        plan = WorkPlan(
            summary="Test",
            owner_uid="test", 
            thread_id="test",
            items={"item1": item1, "item2": item2, "item3": item3, "item4": item4}
        )
        
        # Initially, only items with no dependencies are ready
        ready = plan.get_ready_items()
        ready_ids = {item.id for item in ready}
        assert ready_ids == {"item1", "item3"}
        
        # Mark item1 as done
        item1.status = WorkItemStatus.DONE
        plan.items["item1"] = item1
        
        # Now item2 should be ready, but item4 still blocked
        ready = plan.get_ready_items()
        ready_ids = {item.id for item in ready}
        assert ready_ids == {"item2", "item3"}  # item3 still ready, item2 now ready
        
        # Mark item3 as done
        item3.status = WorkItemStatus.DONE
        plan.items["item3"] = item3
        
        # Now item4 should be ready
        ready = plan.get_ready_items()
        ready_ids = {item.id for item in ready}
        assert ready_ids == {"item2", "item4"}
    
    def test_get_blocked_items(self):
        """Test getting blocked items."""
        item1 = WorkItem(id="item1", title="Task 1", description="Ready")
        item2 = WorkItem(id="item2", title="Task 2", description="Blocked", dependencies=["item1"])
        item3 = WorkItem(id="item3", title="Task 3", description="Multi-blocked", dependencies=["item1", "item2"])
        
        plan = WorkPlan(
            summary="Test",
            owner_uid="test",
            thread_id="test", 
            items={"item1": item1, "item2": item2, "item3": item3}
        )
        
        # Initially, items with dependencies are blocked
        blocked = plan.get_blocked_items()
        blocked_ids = {item.id for item in blocked}
        assert blocked_ids == {"item2", "item3"}
        
        # Mark item1 as done
        item1.status = WorkItemStatus.DONE
        plan.items["item1"] = item1
        
        # Now only item3 is blocked (waiting for item2)
        blocked = plan.get_blocked_items()
        blocked_ids = {item.id for item in blocked}
        assert blocked_ids == {"item3"}
    
    def test_get_status_counts(self):
        """Test getting status counts as Pydantic model."""
        items = {
            "item1": WorkItem(id="item1", title="T1", description="D1", status=WorkItemStatus.PENDING),
            "item2": WorkItem(id="item2", title="T2", description="D2", status=WorkItemStatus.PENDING),
            "item3": WorkItem(id="item3", title="T3", description="D3", status=WorkItemStatus.IN_PROGRESS),
            "item4": WorkItem(id="item4", title="T4", description="D4", status=WorkItemStatus.DONE),
            "item5": WorkItem(id="item5", title="T5", description="D5", status=WorkItemStatus.FAILED),
        }
        
        plan = WorkPlan(
            summary="Test",
            owner_uid="test",
            thread_id="test",
            items=items
        )
        
        counts = plan.get_status_counts()
        assert isinstance(counts, WorkItemStatusCounts)
        assert counts.pending == 2
        assert counts.in_progress == 1
        assert counts.waiting == 0
        assert counts.done == 1
        assert counts.failed == 1
        assert counts.blocked == 0
    
    def test_is_complete(self):
        """Test completion check."""
        # Empty plan is complete
        plan = WorkPlan(summary="Empty", owner_uid="test", thread_id="test")
        assert plan.is_complete()
        
        # Plan with pending items is not complete
        plan.items["item1"] = WorkItem(id="item1", title="T1", description="D1", status=WorkItemStatus.PENDING)
        assert not plan.is_complete()
        
        # Plan with in-progress items is not complete
        plan.items["item1"].status = WorkItemStatus.IN_PROGRESS
        assert not plan.is_complete()
        
        # Plan with waiting items is not complete
        plan.items["item1"].status = WorkItemStatus.WAITING
        assert not plan.is_complete()
        
        # Plan with only done items is complete
        plan.items["item1"].status = WorkItemStatus.DONE
        assert plan.is_complete()
        
        # Plan with done and failed items is complete
        plan.items["item2"] = WorkItem(id="item2", title="T2", description="D2", status=WorkItemStatus.FAILED)
        assert plan.is_complete()
    
    def test_has_local_ready(self):
        """Test checking for local ready items."""
        plan = WorkPlan(summary="Test", owner_uid="test", thread_id="test")
        
        # No items
        assert not plan.has_local_ready()
        
        # Only remote items
        plan.items["remote1"] = WorkItem(
            id="remote1", title="Remote", description="Remote task",
            kind=WorkItemKind.REMOTE, status=WorkItemStatus.PENDING
        )
        assert not plan.has_local_ready()
        
        # Local item but not ready (has dependencies)
        plan.items["local1"] = WorkItem(
            id="local1", title="Local", description="Local task",
            kind=WorkItemKind.LOCAL, status=WorkItemStatus.PENDING,
            dependencies=["remote1"]
        )
        assert not plan.has_local_ready()
        
        # Local item ready (no dependencies)
        plan.items["local2"] = WorkItem(
            id="local2", title="Local Ready", description="Ready local task",
            kind=WorkItemKind.LOCAL, status=WorkItemStatus.PENDING
        )
        assert plan.has_local_ready()
    
    def test_has_remote_waiting(self):
        """Test checking for remote waiting items."""
        plan = WorkPlan(summary="Test", owner_uid="test", thread_id="test")
        
        # No items
        assert not plan.has_remote_waiting()
        
        # Only local items
        plan.items["local1"] = WorkItem(
            id="local1", title="Local", description="Local task",
            kind=WorkItemKind.LOCAL, status=WorkItemStatus.WAITING
        )
        assert not plan.has_remote_waiting()
        
        # Remote item but not waiting
        plan.items["remote1"] = WorkItem(
            id="remote1", title="Remote", description="Remote task",
            kind=WorkItemKind.REMOTE, status=WorkItemStatus.PENDING
        )
        assert not plan.has_remote_waiting()
        
        # Remote item waiting
        plan.items["remote2"] = WorkItem(
            id="remote2", title="Remote Waiting", description="Waiting remote task",
            kind=WorkItemKind.REMOTE, status=WorkItemStatus.WAITING
        )
        assert plan.has_remote_waiting()


class TestToolArguments:
    """Test ToolArguments Pydantic model."""
    
    def test_empty_arguments(self):
        """Test empty tool arguments."""
        args = ToolArguments()
        assert args.model_dump() == {}
    
    def test_tool_arguments_with_data(self):
        """Test tool arguments with various data types."""
        args = ToolArguments(
            string_param="test",
            int_param=42,
            bool_param=True,
            list_param=[1, 2, 3],
            dict_param={"nested": "value"}
        )
        
        assert args.string_param == "test"
        assert args.int_param == 42
        assert args.bool_param is True
        assert args.list_param == [1, 2, 3]
        assert args.dict_param == {"nested": "value"}
    
    def test_tool_arguments_extra_allowed(self):
        """Test that extra fields are allowed."""
        args = ToolArguments(unknown_field="should_work")
        assert args.unknown_field == "should_work"


class TestWorkItemResult:
    """Test WorkItemResult Pydantic model."""
    
    def test_success_result(self):
        """Test successful work item result."""
        result = WorkItemResult(
            success=True,
            content="Task completed successfully",
            artifacts=["output.txt", "report.pdf"],
            metadata={"duration": "2min", "cost": 0.05}
        )
        
        assert result.success is True
        assert result.content == "Task completed successfully"
        assert result.artifacts == ["output.txt", "report.pdf"]
        assert result.metadata == {"duration": "2min", "cost": 0.05}
        assert result.error_details is None
    
    def test_failure_result(self):
        """Test failed work item result."""
        result = WorkItemResult(
            success=False,
            error_details="Connection timeout after 30 seconds"
        )
        
        assert result.success is False
        assert result.content is None
        assert result.artifacts == []
        assert result.metadata == {}
        assert result.error_details == "Connection timeout after 30 seconds"
    
    def test_result_validation(self):
        """Test result validation."""
        # success field is required
        with pytest.raises(ValidationError):
            WorkItemResult()


class TestWorkItemStatusCounts:
    """Test WorkItemStatusCounts Pydantic model."""
    
    def test_default_counts(self):
        """Test default status counts."""
        counts = WorkItemStatusCounts()
        
        assert counts.pending == 0
        assert counts.in_progress == 0
        assert counts.waiting == 0
        assert counts.done == 0
        assert counts.failed == 0
        assert counts.blocked == 0
    
    def test_custom_counts(self):
        """Test custom status counts."""
        counts = WorkItemStatusCounts(
            pending=5,
            in_progress=2,
            waiting=1,
            done=10,
            failed=1,
            blocked=0
        )
        
        assert counts.pending == 5
        assert counts.in_progress == 2
        assert counts.waiting == 1
        assert counts.done == 10
        assert counts.failed == 1
        assert counts.blocked == 0
    
    def test_negative_counts_validation(self):
        """Test that negative counts are not allowed."""
        with pytest.raises(ValidationError):
            WorkItemStatusCounts(pending=-1)
        
        with pytest.raises(ValidationError):
            WorkItemStatusCounts(done=-5)


class TestWorkPlanStatusSummary:
    """Test WorkPlanStatusSummary Pydantic model."""
    
    def test_non_existent_plan_summary(self):
        """Test summary for non-existent plan."""
        summary = WorkPlanStatusSummary(
            exists=False,
            is_complete=False
        )
        
        assert summary.exists is False
        assert summary.total_items == 0
        assert summary.is_complete is False
        assert summary.has_local_ready is False
        assert summary.has_remote_waiting is False
        assert summary.status_counts.pending == 0
    
    def test_active_plan_summary(self):
        """Test summary for active plan."""
        status_counts = WorkItemStatusCounts(
            pending=2, in_progress=1, waiting=1, done=3, failed=0, blocked=1
        )
        
        summary = WorkPlanStatusSummary(
            exists=True,
            total_items=8,
            status_counts=status_counts,
            is_complete=False,
            has_local_ready=True,
            has_remote_waiting=True,
            pending_items=2,
            in_progress_items=1,
            waiting_items=1,
            done_items=3,
            failed_items=0,
            blocked_items=1,
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T01:00:00Z"
        )
        
        assert summary.exists is True
        assert summary.total_items == 8
        assert summary.is_complete is False
        assert summary.has_local_ready is True
        assert summary.has_remote_waiting is True
        assert summary.pending_items == 2
        assert summary.status_counts.pending == 2
        assert summary.status_counts.done == 3
        assert summary.created_at == "2024-01-01T00:00:00Z"
        assert summary.updated_at == "2024-01-01T01:00:00Z"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

