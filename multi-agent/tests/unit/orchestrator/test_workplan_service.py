"""
Unit tests for WorkPlanService.

Tests cover:
- CRUD operations (create, load, save)
- Status management and updates
- Task response handling
- Edge cases and error conditions
- Performance with large plans
"""

import pytest
from unittest.mock import Mock, patch
from typing import Dict, Any

from elements.nodes.common.workload import (
    WorkPlanService, WorkPlan, WorkItem, WorkItemStatus, WorkItemKind,
    WorkItemResult, WorkPlanStatusSummary
)
from tests.fixtures.orchestrator_fixtures import *


class TestWorkPlanServiceBasics:
    """Test basic WorkPlanService functionality."""
    
    def test_service_initialization(self, mock_workload_service):
        """Test WorkPlanService initialization."""
        service = WorkPlanService(mock_workload_service)
        assert service._workload_service == mock_workload_service
    
    def test_create_work_plan(self, work_plan_service):
        """Test creating a new work plan."""
        plan = work_plan_service.create(
            thread_id="test_thread",
            owner_uid="test_owner"
        )
        
        assert isinstance(plan, WorkPlan)
        assert plan.summary == "New Work Plan"
        assert plan.owner_uid == "test_owner"
        assert plan.thread_id == "test_thread"
        assert len(plan.items) == 0
    
    def test_save_and_load_work_plan(self, work_plan_service, sample_work_plan):
        """Test saving and loading work plans."""
        # Save plan
        work_plan_service.save(sample_work_plan)
        
        # Load plan (using new SOLID API)
        loaded_plan = work_plan_service.load(sample_work_plan.thread_id, sample_work_plan.owner_uid)
        
        assert loaded_plan is not None
        assert loaded_plan.summary == sample_work_plan.summary
        assert loaded_plan.owner_uid == sample_work_plan.owner_uid
        assert loaded_plan.thread_id == sample_work_plan.thread_id
        assert len(loaded_plan.items) == len(sample_work_plan.items)
    
    def test_load_nonexistent_plan(self, work_plan_service):
        """Test loading a non-existent work plan."""
        plan = work_plan_service.load("test_thread", "nonexistent_owner")
        assert plan is None
    
    def test_load_corrupted_plan_data(self, work_plan_service, mock_workspace):
        """Test loading corrupted plan data."""
        # Set corrupted data in workspace
        mock_workspace.variables["workplan_corrupted"] = {"invalid": "data"}
        
        plan = work_plan_service.load("test_thread", "corrupted")
        assert plan is None


class TestWorkPlanServiceStatusManagement:
    """Test status management functionality."""
    
    def test_get_status_summary_empty_plan(self, work_plan_service):
        """Test status summary for non-existent plan."""
        summary = work_plan_service.get_status_summary("test_thread", "nonexistent_owner")
        
        assert isinstance(summary, WorkPlanStatusSummary)
        assert summary.total_items == 0
        assert summary.is_complete is False
    
    def test_get_status_summary_complex_plan(self, work_plan_service, complex_work_plan):
        """Test status summary for complex plan."""
        work_plan_service.save(complex_work_plan)
        
        summary = work_plan_service.get_status_summary(complex_work_plan.thread_id, complex_work_plan.owner_uid)
        
        assert summary.total_items == 5
        assert summary.pending_items == 1  # ready_item (no dependencies)
        assert summary.blocked_items == 1  # blocked_item (has unmet dependencies)
        assert summary.waiting_items == 1  # waiting_item
        assert summary.done_items == 1     # done_item
        assert summary.failed_items == 1   # failed_item
        assert summary.has_local_ready is True  # ready_item is LOCAL
        assert summary.has_remote_waiting is True  # waiting_item is REMOTE
        assert summary.is_complete is False  # Not all items done
    
    def test_get_status_summary_complete_plan(self, work_plan_service):
        """Test status summary for completed plan."""
        # Create plan with all items done
        items = {
            "done_item_1": WorkItem(
                id="done_item_1",
                title="Done Item 1",
                description="Completed item",
                status=WorkItemStatus.DONE,
                kind=WorkItemKind.LOCAL
            ),
            "done_item_2": WorkItem(
                id="done_item_2",
                title="Done Item 2", 
                description="Another completed item",
                status=WorkItemStatus.DONE,
                kind=WorkItemKind.REMOTE
            )
        }
        
        complete_plan = WorkPlan(
            summary="Complete Plan",
            owner_uid="complete_owner",
            thread_id="complete_thread",
            items=items
        )
        
        work_plan_service.save(complete_plan)
        summary = work_plan_service.get_status_summary("complete_thread", "complete_owner")
        
        assert summary.total_items == 2
        assert summary.done_items == 2
        assert summary.is_complete is True
    
    def test_update_item_status_success(self, work_plan_service, sample_work_plan):
        """Test successful item status update."""
        work_plan_service.save(sample_work_plan)
        
        success = work_plan_service.update_item_status(
            thread_id=sample_work_plan.thread_id,
            owner_uid=sample_work_plan.owner_uid,
            item_id="item_1",
            status=WorkItemStatus.DONE,
            error=None,
            correlation_task_id="task_123"
        )
        
        assert success is True
        
        # Verify update
        updated_plan = work_plan_service.load(sample_work_plan.thread_id, sample_work_plan.owner_uid)
        item = updated_plan.items["item_1"]
        assert item.status == WorkItemStatus.DONE
        assert item.correlation_task_id == "task_123"
    
    def test_update_item_status_with_error(self, work_plan_service, sample_work_plan):
        """Test item status update with error."""
        work_plan_service.save(sample_work_plan)
        
        success = work_plan_service.update_item_status(
            thread_id=sample_work_plan.thread_id,
            owner_uid=sample_work_plan.owner_uid,
            item_id="item_1",
            status=WorkItemStatus.FAILED,
            error="Task failed due to network error"
        )
        
        assert success is True
        
        # Verify update
        updated_plan = work_plan_service.load(sample_work_plan.thread_id, sample_work_plan.owner_uid)
        item = updated_plan.items["item_1"]
        assert item.status == WorkItemStatus.FAILED
        assert item.error == "Task failed due to network error"
    
    def test_update_item_status_finalize_result(self, work_plan_service, sample_work_plan):
        """Test status update that finalizes result."""
        # Add result to item first
        sample_work_plan.items["item_1"].result_ref = WorkItemResult(
            success=False,
            content="Pending result",
            metadata={"needs_interpretation": True}
        )
        work_plan_service.save(sample_work_plan)
        
        # Update to DONE should finalize result
        success = work_plan_service.update_item_status(
            thread_id=sample_work_plan.thread_id,
            owner_uid=sample_work_plan.owner_uid,
            item_id="item_1",
            status=WorkItemStatus.DONE
        )
        
        assert success is True
        
        # Verify result finalization
        updated_plan = work_plan_service.load(sample_work_plan.thread_id, sample_work_plan.owner_uid)
        item = updated_plan.items["item_1"]
        assert item.status == WorkItemStatus.DONE
        assert item.result_ref.success is True
        assert "needs_interpretation" not in item.result_ref.metadata
    
    def test_update_nonexistent_item(self, work_plan_service, sample_work_plan):
        """Test updating non-existent item."""
        work_plan_service.save(sample_work_plan)
        
        success = work_plan_service.update_item_status(
            thread_id=sample_work_plan.thread_id,
            owner_uid=sample_work_plan.owner_uid,
            item_id="nonexistent_item",
            status=WorkItemStatus.DONE
        )
        
        assert success is False
    
    def test_update_item_nonexistent_plan(self, work_plan_service):
        """Test updating item in non-existent plan."""
        success = work_plan_service.update_item_status(
            thread_id="nonexistent_thread",
            owner_uid="nonexistent_owner",
            item_id="any_item",
            status=WorkItemStatus.DONE
        )
        
        assert success is False


class TestWorkPlanServiceTaskResponses:
    """Test task response handling functionality."""
    
    def test_store_task_response_success(self, work_plan_service, sample_work_plan):
        """Test storing task response for interpretation."""
        # Set up item with correlation ID
        sample_work_plan.items["item_1"].correlation_task_id = "task_123"
        work_plan_service.save(sample_work_plan)
        
        success = work_plan_service.store_task_response(
            thread_id=sample_work_plan.thread_id,
            owner_uid=sample_work_plan.owner_uid,
            correlation_task_id="task_123",
            response_content="I found the data but it needs cleaning",
            from_uid="data_processor"
        )
        
        assert success is True
        
        # Verify response was stored
        updated_plan = work_plan_service.load(sample_work_plan.thread_id, sample_work_plan.owner_uid)
        item = updated_plan.items["item_1"]
        assert item.result_ref is not None
        assert item.result_ref.success is False  # Not finalized
        assert "I found the data but it needs cleaning" in item.result_ref.content
        assert item.result_ref.metadata["from_uid"] == "data_processor"
        assert item.result_ref.metadata["needs_interpretation"] is True
    
    def test_store_task_response_append_content(self, work_plan_service, sample_work_plan):
        """Test appending to existing response content."""
        # Set up item with existing result
        sample_work_plan.items["item_1"].correlation_task_id = "task_123"
        sample_work_plan.items["item_1"].result_ref = WorkItemResult(
            success=False,
            content="First response",
            metadata={"from_uid": "node_1"}
        )
        work_plan_service.save(sample_work_plan)
        
        # Store additional response
        success = work_plan_service.store_task_response(
            thread_id=sample_work_plan.thread_id,
            owner_uid=sample_work_plan.owner_uid,
            correlation_task_id="task_123",
            response_content="Second response with more details",
            from_uid="node_2"
        )
        
        assert success is True
        
        # Verify content was appended
        updated_plan = work_plan_service.load(sample_work_plan.thread_id, sample_work_plan.owner_uid)
        item = updated_plan.items["item_1"]
        assert "First response" in item.result_ref.content
        assert "Second response with more details" in item.result_ref.content
        assert "--- Response from node_2 ---" in item.result_ref.content
        assert item.result_ref.metadata["needs_interpretation"] is True
    
    def test_store_task_response_no_correlation_id(self, work_plan_service, sample_work_plan):
        """Test storing response with no matching correlation ID."""
        work_plan_service.save(sample_work_plan)
        
        success = work_plan_service.store_task_response(
            thread_id=sample_work_plan.thread_id,
            owner_uid=sample_work_plan.owner_uid,
            correlation_task_id="nonexistent_task",
            response_content="Response content",
            from_uid="some_node"
        )
        
        assert success is False
    
    def test_ingest_task_response_explicit_success(self, work_plan_service, sample_work_plan):
        """Test ingesting explicit success response."""
        # Set up item with correlation ID
        sample_work_plan.items["item_1"].correlation_task_id = "task_123"
        sample_work_plan.items["item_1"].status = WorkItemStatus.WAITING
        work_plan_service.save(sample_work_plan)
        
        success =         work_plan_service.ingest_task_response(
            thread_id=sample_work_plan.thread_id,
            owner_uid=sample_work_plan.owner_uid,
            correlation_task_id="task_123",
            result={"success": True, "data": {"value": 42}}
        )
        
        assert success is True
        
        # Verify item was marked as DONE
        updated_plan = work_plan_service.load(sample_work_plan.thread_id, sample_work_plan.owner_uid)
        item = updated_plan.items["item_1"]
        assert item.status == WorkItemStatus.DONE
        assert item.result_ref is not None
        assert item.result_ref.success is True
        assert item.result_ref.data == {"success": True, "data": {"value": 42}}
    
    def test_ingest_task_response_explicit_error(self, work_plan_service, sample_work_plan):
        """Test ingesting explicit error response."""
        # Set up item with correlation ID
        sample_work_plan.items["item_1"].correlation_task_id = "task_123"
        sample_work_plan.items["item_1"].status = WorkItemStatus.WAITING
        work_plan_service.save(sample_work_plan)
        
        success =         work_plan_service.ingest_task_response(
            thread_id=sample_work_plan.thread_id,
            owner_uid=sample_work_plan.owner_uid,
            correlation_task_id="task_123",
            error="Network connection failed"
        )
        
        assert success is True
        
        # Verify item was marked as FAILED
        updated_plan = work_plan_service.load(sample_work_plan.thread_id, sample_work_plan.owner_uid)
        item = updated_plan.items["item_1"]
        assert item.status == WorkItemStatus.FAILED
        assert item.error == "Network connection failed"
    
    def test_ingest_task_response_increment_retry(self, work_plan_service, sample_work_plan):
        """Test response ingestion increments retry count."""
        # Set up item with correlation ID
        sample_work_plan.items["item_1"].correlation_task_id = "task_123"
        sample_work_plan.items["item_1"].status = WorkItemStatus.WAITING
        sample_work_plan.items["item_1"].retry_count = 1
        work_plan_service.save(sample_work_plan)
        
        success =         work_plan_service.ingest_task_response(
            thread_id=sample_work_plan.thread_id,
            owner_uid=sample_work_plan.owner_uid,
            correlation_task_id="task_123",
            error="Temporary failure"
        )
        
        assert success is True
        
        # Verify retry count was incremented
        updated_plan = work_plan_service.load(sample_work_plan.thread_id, sample_work_plan.owner_uid)
        item = updated_plan.items["item_1"]
        assert item.retry_count == 2
    
    def test_mark_item_as_delegated(self, work_plan_service, sample_work_plan):
        """Test marking item as delegated."""
        work_plan_service.save(sample_work_plan)
        
        success =         work_plan_service.mark_item_as_delegated(
            thread_id=sample_work_plan.thread_id,
            owner_uid=sample_work_plan.owner_uid,
            item_id="item_1",
            correlation_task_id="task_456"
        )
        
        assert success is True
        
        # Verify item was updated
        updated_plan = work_plan_service.load(sample_work_plan.thread_id, sample_work_plan.owner_uid)
        item = updated_plan.items["item_1"]
        assert item.status == WorkItemStatus.WAITING
        assert item.correlation_task_id == "task_456"
    
    def test_mark_nonexistent_item_as_delegated(self, work_plan_service, sample_work_plan):
        """Test marking non-existent item as delegated."""
        work_plan_service.save(sample_work_plan)
        
        success =         work_plan_service.mark_item_as_delegated(
            thread_id=sample_work_plan.thread_id,
            owner_uid=sample_work_plan.owner_uid,
            item_id="nonexistent_item",
            correlation_task_id="task_456"
        )
        
        assert success is False


class TestWorkPlanServiceEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_service_with_failing_workspace(self):
        """Test service behavior with failing workspace operations."""
        failing_workspace = Mock()
        failing_workspace.get_variable.side_effect = Exception("Workspace error")
        failing_workspace.set_variable.side_effect = Exception("Workspace error")
        
        # Create failing workload service for SOLID design
        failing_workload_service = Mock()
        failing_workload_service.get_workspace.return_value = failing_workspace
        failing_workload_service.update_workspace.side_effect = Exception("Workload service error")
        
        service = WorkPlanService(failing_workload_service)
        
        # Load should handle workspace errors gracefully
        plan = service.load("test_thread", "test_owner")
        assert plan is None
        
        # Save should handle workspace errors gracefully
        test_plan = WorkPlan(
            summary="Test Plan",
            owner_uid="test_owner",
            thread_id="test_thread"
        )
        
        # Should not raise exception
        try:
            service.save(test_plan)
        except Exception:
            pytest.fail("Save should handle workspace errors gracefully")
    
    def test_concurrent_plan_modifications(self, work_plan_service, sample_work_plan):
        """Test concurrent modifications to the same plan."""
        work_plan_service.save(sample_work_plan)
        
        # Simulate concurrent access
        plan1 = work_plan_service.load(sample_work_plan.thread_id, sample_work_plan.owner_uid)
        plan2 = work_plan_service.load(sample_work_plan.thread_id, sample_work_plan.owner_uid)
        
        # Modify both plans
        plan1.items["item_1"].status = WorkItemStatus.IN_PROGRESS
        plan2.items["item_2"].status = WorkItemStatus.DONE
        
        # Save both (last one wins)
        work_plan_service.save(plan1)
        work_plan_service.save(plan2)
        
        # Verify final state
        final_plan = work_plan_service.load(sample_work_plan.thread_id, sample_work_plan.owner_uid)
        # plan2 was saved last, so item_2 should be DONE
        # but item_1 changes from plan1 are lost
        assert final_plan.items["item_2"].status == WorkItemStatus.DONE
        assert final_plan.items["item_1"].status == WorkItemStatus.PENDING  # Original state
    
    def test_large_plan_performance(self, work_plan_service, large_work_plan):
        """Test performance with large work plans."""
        # Save large plan
        work_plan_service.save(large_work_plan)
        
        # Load should still work efficiently
        loaded_plan = work_plan_service.load(large_work_plan.thread_id, large_work_plan.owner_uid)
        assert loaded_plan is not None
        assert len(loaded_plan.items) == 100
        
        # Status summary should work efficiently
        summary = work_plan_service.get_status_summary(large_work_plan.thread_id, large_work_plan.owner_uid)
        assert summary.total_items == 100
    
    def test_malformed_response_data(self, work_plan_service, sample_work_plan):
        """Test handling of malformed response data."""
        # Set up item
        sample_work_plan.items["item_1"].correlation_task_id = "task_123"
        work_plan_service.save(sample_work_plan)
        
        # Store malformed response
        success = work_plan_service.store_task_response(
            thread_id=sample_work_plan.thread_id,
            owner_uid=sample_work_plan.owner_uid,
            correlation_task_id="task_123",
            response_content="",  # Empty response
            from_uid=""  # Empty from_uid
        )
        
        assert success is True
        
        # Verify it was stored despite being malformed
        updated_plan = work_plan_service.load(sample_work_plan.thread_id, sample_work_plan.owner_uid)
        item = updated_plan.items["item_1"]
        assert item.result_ref is not None
        assert item.result_ref.metadata["needs_interpretation"] is True
    
    def test_unicode_and_special_characters(self, work_plan_service):
        """Test handling of unicode and special characters."""
        # Create plan with unicode content
        unicode_plan = WorkPlan(
            summary="Plan with 🚀 emojis and ñoñó special chars",
            owner_uid="unicode_owner",
            thread_id="unicode_thread",
            items={
                "unicode_item": WorkItem(
                    id="unicode_item",
                    title="Item with 中文 characters",
                    description="Description with \n newlines and \t tabs"
                )
            }
        )
        
        # Should save and load correctly
        work_plan_service.save(unicode_plan)
        loaded_plan = work_plan_service.load("unicode_thread", "unicode_owner")
        
        assert loaded_plan is not None
        assert "🚀" in loaded_plan.summary
        assert "中文" in loaded_plan.items["unicode_item"].title
        assert "\n" in loaded_plan.items["unicode_item"].description
    
    def test_memory_usage_with_large_responses(self, work_plan_service, sample_work_plan):
        """Test memory usage with very large response content."""
        # Set up item
        sample_work_plan.items["item_1"].correlation_task_id = "task_123"
        work_plan_service.save(sample_work_plan)
        
        # Store very large response
        large_content = "x" * 1000000  # 1MB of content
        success = work_plan_service.store_task_response(
            thread_id=sample_work_plan.thread_id,
            owner_uid=sample_work_plan.owner_uid,
            correlation_task_id="task_123",
            response_content=large_content,
            from_uid="large_node"
        )
        
        assert success is True
        
        # Should still be able to load and work with the plan
        updated_plan = work_plan_service.load(sample_work_plan.thread_id, sample_work_plan.owner_uid)
        assert updated_plan is not None
        assert len(updated_plan.items["item_1"].result_ref.content) >= 1000000


class TestWorkPlanServiceDebugOutput:
    """Test debug output and logging functionality."""
    
    def test_debug_output_on_operations(self, work_plan_service, sample_work_plan, capture_debug_output):
        """Test that debug output is generated for operations."""
        # Save operation should generate debug output
        work_plan_service.save(sample_work_plan)
        
        debug_messages = capture_debug_output
        save_messages = [msg for msg in debug_messages if "[PLAN] Saved:" in msg]
        assert len(save_messages) > 0
        
        # Load operation should generate debug output
        work_plan_service.load(sample_work_plan.thread_id, sample_work_plan.owner_uid)
        
        load_messages = [msg for msg in debug_messages if "[PLAN] Loaded:" in msg]
        assert len(load_messages) > 0
    
    def test_debug_output_on_status_operations(self, work_plan_service, sample_work_plan, capture_debug_output):
        """Test debug output for status operations."""
        work_plan_service.save(sample_work_plan)
        
        # Update item status should generate debug output
        work_plan_service.update_item_status(
            thread_id=sample_work_plan.thread_id,
            owner_uid=sample_work_plan.owner_uid,
            item_id="item_1",
            status=WorkItemStatus.DONE
        )
        
        debug_messages = capture_debug_output
        update_messages = [msg for msg in debug_messages if "update_item_status()" in msg]
        assert len(update_messages) > 0
    
    def test_debug_output_on_response_operations(self, work_plan_service, sample_work_plan, capture_debug_output):
        """Test debug output for response operations."""
        sample_work_plan.items["item_1"].correlation_task_id = "task_123"
        work_plan_service.save(sample_work_plan)
        
        # Store response should generate debug output
        work_plan_service.store_task_response(
            thread_id=sample_work_plan.thread_id,
            owner_uid=sample_work_plan.owner_uid,
            correlation_task_id="task_123",
            response_content="Test response",
            from_uid="test_node"
        )
        
        debug_messages = capture_debug_output
        store_messages = [msg for msg in debug_messages if "store_task_response()" in msg]
        assert len(store_messages) > 0
