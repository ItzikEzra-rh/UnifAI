"""
Unit tests for WorkPlan and WorkItem Pydantic models.

Tests cover:
- Model validation and serialization
- Business logic methods
- Edge cases and error conditions
- Status transitions
- Dependency management
"""

import pytest
from datetime import datetime
from typing import Set
from pydantic import ValidationError

from elements.nodes.common.workload import (
    WorkPlan, WorkItem, WorkItemStatus, WorkItemKind,
    WorkItemResult, ToolArguments, WorkPlanStatusSummary
)
from tests.fixtures.orchestrator_fixtures import *


class TestWorkItem:
    """Test WorkItem model and its methods."""
    
    def test_work_item_creation(self, sample_work_item):
        """Test basic WorkItem creation and validation."""
        assert sample_work_item.id == "test_item_1"
        assert sample_work_item.title == "Test Work Item"
        assert sample_work_item.status == WorkItemStatus.PENDING
        assert sample_work_item.kind == WorkItemKind.REMOTE
        assert sample_work_item.retry_count == 0
        assert sample_work_item.max_retries == 3
        assert sample_work_item.dependencies == ["dependency_1"]
    
    def test_work_item_defaults(self):
        """Test WorkItem default values."""
        item = WorkItem(
            id="minimal_item",
            title="Minimal Item",
            description="Minimal work item"
        )
        
        assert item.status == WorkItemStatus.PENDING
        assert item.kind == WorkItemKind.LOCAL
        assert item.dependencies == []
        assert item.retry_count == 0
        assert item.max_retries == 3
        assert item.assigned_uid is None
        assert item.tool is None
        assert item.result_ref is None
        assert item.error is None
    
    def test_work_item_validation_errors(self):
        """Test WorkItem validation errors."""
        # Missing required fields
        with pytest.raises(ValidationError) as exc_info:
            WorkItem()
        
        errors = exc_info.value.errors()
        required_fields = {error['loc'][0] for error in errors if error['type'] == 'missing'}
        assert 'id' in required_fields
        assert 'title' in required_fields
        assert 'description' in required_fields
    
    def test_is_ready_for_execution(self):
        """Test is_ready_for_execution logic."""
        # Item with no dependencies should be ready
        item_no_deps = WorkItem(
            id="ready_item",
            title="Ready Item",
            description="Ready for execution",
            status=WorkItemStatus.PENDING
        )
        assert item_no_deps.is_ready_for_execution(set())
        
        # Item with satisfied dependencies should be ready
        item_with_deps = WorkItem(
            id="dependent_item",
            title="Dependent Item", 
            description="Has dependencies",
            dependencies=["dep1", "dep2"],
            status=WorkItemStatus.PENDING
        )
        completed_ids = {"dep1", "dep2", "other_item"}
        assert item_with_deps.is_ready_for_execution(completed_ids)
        
        # Item with unsatisfied dependencies should not be ready
        incomplete_ids = {"dep1"}
        assert not item_with_deps.is_ready_for_execution(incomplete_ids)
        
        # Non-pending items should not be ready
        item_in_progress = WorkItem(
            id="in_progress_item",
            title="In Progress Item",
            description="Already in progress",
            status=WorkItemStatus.IN_PROGRESS
        )
        assert not item_in_progress.is_ready_for_execution(set())
    
    def test_is_blocked(self):
        """Test is_blocked logic."""
        # Item with unsatisfied dependencies should be blocked
        blocked_item = WorkItem(
            id="blocked_item",
            title="Blocked Item",
            description="Blocked by dependencies",
            dependencies=["missing_dep"],
            status=WorkItemStatus.PENDING
        )
        assert blocked_item.is_blocked(set())
        assert blocked_item.is_blocked({"other_item"})
        
        # Item with satisfied dependencies should not be blocked
        assert not blocked_item.is_blocked({"missing_dep"})
        
        # Item with no dependencies should not be blocked
        unblocked_item = WorkItem(
            id="unblocked_item",
            title="Unblocked Item",
            description="No dependencies",
            status=WorkItemStatus.PENDING
        )
        assert not unblocked_item.is_blocked(set())
    
    def test_can_retry(self):
        """Test can_retry logic."""
        # Item under retry limit should be retryable
        retryable_item = WorkItem(
            id="retryable_item",
            title="Retryable Item",
            description="Can be retried",
            retry_count=1,
            max_retries=3
        )
        assert retryable_item.can_retry()
        
        # Item at retry limit should not be retryable
        max_retry_item = WorkItem(
            id="max_retry_item",
            title="Max Retry Item",
            description="At max retries",
            retry_count=3,
            max_retries=3
        )
        assert not max_retry_item.can_retry()
        
        # Item over retry limit should not be retryable
        over_limit_item = WorkItem(
            id="over_limit_item",
            title="Over Limit Item",
            description="Over retry limit",
            retry_count=5,
            max_retries=3
        )
        assert not over_limit_item.can_retry()
    
    def test_increment_retry(self):
        """Test increment_retry functionality."""
        item = WorkItem(
            id="retry_item",
            title="Retry Item",
            description="For retry testing",
            retry_count=0
        )
        
        # Should increment retry count
        item.increment_retry()
        assert item.retry_count == 1
        
        # Should update timestamp
        old_updated_at = item.updated_at
        item.increment_retry()
        assert item.retry_count == 2
        assert item.updated_at != old_updated_at
    
    def test_mark_updated(self):
        """Test mark_updated functionality."""
        item = WorkItem(
            id="update_item",
            title="Update Item",
            description="For update testing"
        )
        
        old_updated_at = item.updated_at
        item.mark_updated()
        assert item.updated_at != old_updated_at
    
    def test_work_item_serialization(self, sample_work_item):
        """Test WorkItem serialization and deserialization."""
        # Serialize to dict
        item_dict = sample_work_item.model_dump()
        assert isinstance(item_dict, dict)
        assert item_dict['id'] == "test_item_1"
        assert item_dict['status'] == WorkItemStatus.PENDING.value
        
        # Deserialize from dict
        restored_item = WorkItem(**item_dict)
        assert restored_item.id == sample_work_item.id
        assert restored_item.title == sample_work_item.title
        assert restored_item.status == sample_work_item.status
    
    def test_work_item_with_result(self, sample_work_item_with_result):
        """Test WorkItem with result data."""
        item = sample_work_item_with_result
        
        assert item.status == WorkItemStatus.DONE
        assert item.result_ref is not None
        assert item.result_ref.success is True
        assert item.result_ref.content == "Task completed successfully"
        assert item.result_ref.data == {"output": "test result"}
        assert item.result_ref.metadata == {"execution_time": 1.5}
    
    @pytest.mark.parametrize("status", [
        WorkItemStatus.PENDING,
        WorkItemStatus.IN_PROGRESS,
        WorkItemStatus.WAITING,
        WorkItemStatus.DONE,
        WorkItemStatus.FAILED
    ])
    def test_work_item_all_statuses(self, status):
        """Test WorkItem with all possible statuses."""
        item = WorkItem(
            id=f"item_{status.value}",
            title=f"Item {status.value}",
            description=f"Item with status {status.value}",
            status=status
        )
        assert item.status == status
    
    @pytest.mark.parametrize("kind", [WorkItemKind.LOCAL, WorkItemKind.REMOTE])
    def test_work_item_all_kinds(self, kind):
        """Test WorkItem with all possible kinds."""
        item = WorkItem(
            id=f"item_{kind.value}",
            title=f"Item {kind.value}",
            description=f"Item with kind {kind.value}",
            kind=kind
        )
        assert item.kind == kind


class TestWorkPlan:
    """Test WorkPlan model and its methods."""
    
    def test_work_plan_creation(self, sample_work_plan):
        """Test basic WorkPlan creation."""
        plan = sample_work_plan
        
        assert plan.summary == "Test Work Plan"
        assert plan.owner_uid == "test_orchestrator"
        assert plan.thread_id == "test_thread_123"
        assert len(plan.items) == 3
        assert "item_1" in plan.items
        assert "item_2" in plan.items
        assert "item_3" in plan.items
    
    def test_work_plan_defaults(self):
        """Test WorkPlan default values."""
        plan = WorkPlan(
            summary="Minimal Plan",
            owner_uid="test_owner",
            thread_id="test_thread"
        )
        
        assert plan.items == {}
        assert plan.created_at is not None
        assert plan.updated_at is not None
    
    def test_get_completed_item_ids(self, complex_work_plan):
        """Test get_completed_item_ids method."""
        plan = complex_work_plan
        completed_ids = plan.get_completed_item_ids()
        
        assert isinstance(completed_ids, set)
        assert "done_item" in completed_ids
        assert "failed_item" in completed_ids
        assert "ready_item" not in completed_ids
        assert "waiting_item" not in completed_ids
        assert "blocked_item" not in completed_ids
    
    def test_get_ready_items(self, complex_work_plan):
        """Test get_ready_items method."""
        plan = complex_work_plan
        ready_items = plan.get_ready_items()
        
        # Should include items with no dependencies and PENDING status
        ready_ids = {item.id for item in ready_items}
        assert "ready_item" in ready_ids
        
        # Should not include items with unsatisfied dependencies
        assert "blocked_item" not in ready_ids
        
        # Should not include items that are not PENDING
        assert "waiting_item" not in ready_ids
        assert "done_item" not in ready_ids
        assert "failed_item" not in ready_ids
    
    def test_get_blocked_items(self, complex_work_plan):
        """Test get_blocked_items method."""
        plan = complex_work_plan
        blocked_items = plan.get_blocked_items()
        
        blocked_ids = {item.id for item in blocked_items}
        assert "blocked_item" in blocked_ids
        
        # Items with satisfied dependencies should not be blocked
        assert "ready_item" not in blocked_ids
    
    def test_get_items_by_status(self, complex_work_plan):
        """Test get_items_by_status method."""
        plan = complex_work_plan
        
        # Test each status
        pending_items = plan.get_items_by_status(WorkItemStatus.PENDING)
        pending_ids = {item.id for item in pending_items}
        assert "ready_item" in pending_ids
        assert "blocked_item" in pending_ids
        
        waiting_items = plan.get_items_by_status(WorkItemStatus.WAITING)
        waiting_ids = {item.id for item in waiting_items}
        assert "waiting_item" in waiting_ids
        
        done_items = plan.get_items_by_status(WorkItemStatus.DONE)
        done_ids = {item.id for item in done_items}
        assert "done_item" in done_ids
        
        failed_items = plan.get_items_by_status(WorkItemStatus.FAILED)
        failed_ids = {item.id for item in failed_items}
        assert "failed_item" in failed_ids
    
    def test_get_status_counts(self, complex_work_plan):
        """Test get_status_counts method."""
        plan = complex_work_plan
        counts = plan.get_status_counts()
        
        assert counts.pending == 1  # ready_item (no dependencies)
        assert counts.blocked == 1  # blocked_item (has unmet dependencies)
        assert counts.in_progress == 0
        assert counts.waiting == 1   # waiting_item
        assert counts.done == 1      # done_item
        assert counts.failed == 1    # failed_item
        
        assert counts.total == 5
    
    def test_mark_updated(self, sample_work_plan):
        """Test mark_updated functionality."""
        plan = sample_work_plan
        old_updated_at = plan.updated_at
        
        plan.mark_updated()
        assert plan.updated_at != old_updated_at
    
    def test_work_plan_serialization(self, sample_work_plan):
        """Test WorkPlan serialization and deserialization."""
        # Serialize to dict
        plan_dict = sample_work_plan.model_dump()
        assert isinstance(plan_dict, dict)
        assert plan_dict['summary'] == "Test Work Plan"
        assert plan_dict['owner_uid'] == "test_orchestrator"
        assert len(plan_dict['items']) == 3
        
        # Deserialize from dict
        restored_plan = WorkPlan(**plan_dict)
        assert restored_plan.summary == sample_work_plan.summary
        assert restored_plan.owner_uid == sample_work_plan.owner_uid
        assert len(restored_plan.items) == len(sample_work_plan.items)
    
    def test_empty_work_plan(self, empty_work_plan):
        """Test empty WorkPlan behavior."""
        plan = empty_work_plan
        
        assert len(plan.items) == 0
        assert plan.get_completed_item_ids() == set()
        assert plan.get_ready_items() == []
        assert plan.get_blocked_items() == []
        
        counts = plan.get_status_counts()
        assert counts.total == 0
        assert counts.pending == 0
        assert counts.done == 0
    
    def test_circular_dependencies(self, circular_dependency_work_plan):
        """Test WorkPlan with circular dependencies."""
        plan = circular_dependency_work_plan
        
        # All items should be blocked due to circular dependencies
        ready_items = plan.get_ready_items()
        assert len(ready_items) == 0
        
        blocked_items = plan.get_blocked_items()
        assert len(blocked_items) == 3
        
        # All items should be pending but blocked
        pending_items = plan.get_items_by_status(WorkItemStatus.PENDING)
        assert len(pending_items) == 3


class TestWorkItemResult:
    """Test WorkItemResult model."""
    
    def test_work_item_result_creation(self):
        """Test WorkItemResult creation and validation."""
        result = WorkItemResult(
            success=True,
            content="Task completed",
            data={"key": "value"},
            metadata={"duration": 1.5, "from_uid": "test_node"}
        )
        
        assert result.success is True
        assert result.content == "Task completed"
        assert result.data == {"key": "value"}
        assert result.metadata == {"duration": 1.5, "from_uid": "test_node"}
        assert result.artifacts == []
    
    def test_work_item_result_defaults(self):
        """Test WorkItemResult default values."""
        result = WorkItemResult()
        
        assert result.success is True  # Default to success (optimistic)
        assert result.content is None  # Default to None, not empty string
        assert result.data is None     # Default to None, not empty dict
        assert result.artifacts == []  # Default to empty list
        assert result.metadata == {}   # Default to empty dict


class TestToolArguments:
    """Test ToolArguments model."""
    
    def test_tool_arguments_creation(self):
        """Test ToolArguments creation."""
        args = ToolArguments({"param1": "value1", "param2": 42})
        
        assert args["param1"] == "value1"
        assert args["param2"] == 42
    
    def test_tool_arguments_defaults(self):
        """Test ToolArguments default behavior."""
        args = ToolArguments()
        assert len(args) == 0
        
        # Should behave like a dict
        args["new_param"] = "new_value"
        assert args["new_param"] == "new_value"


class TestWorkPlanStatusSummary:
    """Test WorkPlanStatusSummary model."""
    
    def test_status_summary_creation(self):
        """Test WorkPlanStatusSummary creation."""
        summary = WorkPlanStatusSummary(
            total_items=10,
            pending_items=3,
            in_progress_items=2,
            waiting_items=1,
            done_items=3,
            failed_items=1,
            blocked_items=0,
            has_local_ready=True,
            has_remote_waiting=True,
            is_complete=False
        )
        
        assert summary.total_items == 10
        assert summary.pending_items == 3
        assert summary.done_items == 3
        assert summary.has_local_ready is True
        assert summary.is_complete is False
    
    def test_status_summary_defaults(self):
        """Test WorkPlanStatusSummary default values."""
        summary = WorkPlanStatusSummary()
        
        assert summary.total_items == 0
        assert summary.pending_items == 0
        assert summary.in_progress_items == 0
        assert summary.waiting_items == 0
        assert summary.done_items == 0
        assert summary.failed_items == 0
        assert summary.blocked_items == 0
        assert summary.has_local_ready is False
        assert summary.has_remote_waiting is False
        assert summary.is_complete is False


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_work_item_extreme_values(self):
        """Test WorkItem with extreme values."""
        # Very long strings
        long_string = "x" * 10000
        item = WorkItem(
            id="extreme_item",
            title=long_string,
            description=long_string
        )
        assert len(item.title) == 10000
        assert len(item.description) == 10000
        
        # Large retry counts
        item.retry_count = 999999
        item.max_retries = 1000000
        assert item.can_retry()
        
        # Many dependencies
        many_deps = [f"dep_{i}" for i in range(1000)]
        item.dependencies = many_deps
        assert len(item.dependencies) == 1000
    
    def test_work_plan_extreme_values(self, large_work_plan):
        """Test WorkPlan with many items."""
        plan = large_work_plan
        
        assert len(plan.items) == 100
        
        # Should still work correctly
        ready_items = plan.get_ready_items()
        assert len(ready_items) == 1  # Only first item has no dependencies
        
        counts = plan.get_status_counts()
        assert counts.total == 100
        assert counts.pending == 1    # Only item_0 has no dependencies
        assert counts.blocked == 99   # Items 1-99 are blocked by dependency chain
    
    def test_invalid_dependencies(self):
        """Test handling of invalid dependency references."""
        # WorkItem with non-existent dependencies
        item = WorkItem(
            id="invalid_deps_item",
            title="Invalid Dependencies",
            description="Has invalid dependencies",
            dependencies=["non_existent_1", "non_existent_2"]
        )
        
        # Should be blocked since dependencies don't exist
        assert item.is_blocked(set())
        assert not item.is_ready_for_execution(set())
    
    def test_concurrent_modifications(self, sample_work_plan):
        """Test behavior under concurrent modifications."""
        plan = sample_work_plan
        
        # Simulate concurrent access
        original_count = len(plan.items)
        
        # Add item while iterating (simulates concurrent modification)
        ready_items = []
        for item in plan.get_ready_items():
            ready_items.append(item)
            # Add new item during iteration
            plan.items[f"concurrent_item_{len(plan.items)}"] = WorkItem(
                id=f"concurrent_item_{len(plan.items)}",
                title="Concurrent Item",
                description="Added during iteration"
            )
        
        # Should handle gracefully
        assert len(plan.items) > original_count
