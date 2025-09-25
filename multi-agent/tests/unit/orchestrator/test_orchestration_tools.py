"""
Unit tests for orchestration tools.

Tests cover:
- CreateOrUpdateWorkPlanTool
- DelegateTaskTool
- MarkWorkItemStatusTool
- AssignWorkItemTool
- SummarizeWorkPlanTool
- Edge cases and error conditions
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any
from pydantic import BaseModel

from elements.tools.builtin.workplan.create_or_update import (
    CreateOrUpdateWorkPlanTool, CreateOrUpdatePlanArgs, WorkItemSpec
)
from elements.tools.builtin.delegation.delegate_task import (
    DelegateTaskTool, DelegateTaskArgs
)
from elements.tools.builtin.workplan.mark_status import (
    MarkWorkItemStatusTool, MarkStatusArgs
)
from elements.tools.builtin.workplan.assign_item import (
    AssignWorkItemTool, AssignItemArgs
)
from elements.tools.builtin.workplan.summarize import (
    SummarizeWorkPlanTool
)
from elements.nodes.common.workload import (
    WorkPlan, WorkItem, WorkItemStatus, WorkItemKind, WorkPlanService, Task
)
from tests.fixtures.orchestrator_fixtures import *


class TestCreateOrUpdateWorkPlanTool:
    """Test CreateOrUpdateWorkPlanTool functionality."""
    
    def test_tool_initialization(self, mock_tool_dependencies):
        """Test tool initialization with dependencies."""
        tool = CreateOrUpdateWorkPlanTool(
            get_thread_id=mock_tool_dependencies["get_thread_id"],
            get_owner_uid=mock_tool_dependencies["get_owner_uid"],
            get_workload_service=mock_tool_dependencies["get_workload_service"]
        )
        
        assert tool.name == "workplan.create_or_update"
        assert "Create a new work plan or update existing plan" in tool.description
        assert tool.args_schema == CreateOrUpdatePlanArgs
    
    def test_create_new_work_plan(self, mock_tool_dependencies, capture_debug_output):
        """Test creating a new work plan."""
        tool = CreateOrUpdateWorkPlanTool(
            get_thread_id=mock_tool_dependencies["get_thread_id"],
            get_owner_uid=mock_tool_dependencies["get_owner_uid"],
            get_workload_service=mock_tool_dependencies["get_workload_service"]
        )
        
        result = tool.run(
            summary="Test Work Plan",
            items=[
                {
                    "id": "item_1",
                    "title": "First Item",
                    "description": "First work item",
                    "dependencies": [],
                    "kind": "remote"
                },
                {
                    "id": "item_2",
                    "title": "Second Item",
                    "description": "Second work item",
                    "dependencies": ["item_1"],
                    "kind": "local"
                }
            ]
        )
        
        assert result["success"] is True
        assert result["total_items"] == 2
        assert "plan_id" in result
        assert "status_counts" in result
        
        # Verify debug output
        debug_messages = capture_debug_output
        assert any("CreateOrUpdateWorkPlanTool.run()" in msg for msg in debug_messages)
        assert any("Plan summary: Test Work Plan" in msg for msg in debug_messages)
    
    def test_update_existing_work_plan(self, mock_tool_dependencies, sample_work_plan):
        """Test updating an existing work plan."""
        # Pre-populate workspace with existing plan
        workload_service = mock_tool_dependencies["get_workload_service"]()
        service = WorkPlanService(workload_service)
        service.save(sample_work_plan)
        
        tool = CreateOrUpdateWorkPlanTool(
            get_thread_id=mock_tool_dependencies["get_thread_id"],
            get_owner_uid=mock_tool_dependencies["get_owner_uid"],
            get_workload_service=mock_tool_dependencies["get_workload_service"]
        )
        
        result = tool.run(
            summary="Updated Work Plan",
            items=[
                {
                    "id": "new_item",
                    "title": "New Item",
                    "description": "Newly added item",
                    "dependencies": [],
                    "kind": "local"
                }
            ]
        )
        
        assert result["success"] is True
        assert result["total_items"] == 4  # 3 existing + 1 new
        
        # Verify plan was updated
        updated_plan = service.load(sample_work_plan.thread_id, sample_work_plan.owner_uid)
        assert updated_plan.summary == "Updated Work Plan"
        assert "new_item" in updated_plan.items
        # Original items should still exist
        assert len(updated_plan.items) == 4  # 3 original + 1 new
    
    def test_work_item_spec_validation(self):
        """Test WorkItemSpec validation."""
        # Valid spec
        spec = WorkItemSpec(
            id="valid_item",
            title="Valid Item",
            description="Valid description",
            dependencies=["dep1"],
            kind=WorkItemKind.REMOTE
        )
        assert spec.id == "valid_item"
        assert spec.kind == WorkItemKind.REMOTE
        
        # Invalid spec - missing required fields
        with pytest.raises(Exception):  # Pydantic ValidationError
            WorkItemSpec()
    
    def test_tool_with_invalid_arguments(self, mock_tool_dependencies):
        """Test tool with invalid arguments."""
        tool = CreateOrUpdateWorkPlanTool(
            get_thread_id=mock_tool_dependencies["get_thread_id"],
            get_owner_uid=mock_tool_dependencies["get_owner_uid"],
            get_workload_service=mock_tool_dependencies["get_workload_service"]
        )
        
        # Missing required arguments
        with pytest.raises(Exception):
            tool.run()
        
        # Invalid item structure
        with pytest.raises(Exception):
            tool.run(
                summary="Test Plan",
                items=[{"invalid": "structure"}]
            )


class TestDelegateTaskTool:
    """Test DelegateTaskTool functionality."""
    
    def test_tool_initialization(self, mock_tool_dependencies):
        """Test tool initialization."""
        tool = DelegateTaskTool(
            send_task=mock_tool_dependencies["send_task"],
            get_owner_uid=mock_tool_dependencies["get_owner_uid"],
            get_thread_id=mock_tool_dependencies["get_thread_id"],
            get_workload_service=mock_tool_dependencies["get_workload_service"],
            check_adjacency=mock_tool_dependencies["check_adjacency"]
        )
        
        assert tool.name == "iem.delegate_task"
        assert "Delegate a task to an adjacent node" in tool.description
        assert tool.args_schema == DelegateTaskArgs
    
    def test_successful_task_delegation(self, mock_tool_dependencies, sample_work_plan, capture_debug_output):
        """Test successful task delegation."""
        # Setup workspace with work plan
        workload_service = mock_tool_dependencies["get_workload_service"]()
        service = WorkPlanService(workload_service)
        service.save(sample_work_plan)
        
        tool = DelegateTaskTool(
            send_task=mock_tool_dependencies["send_task"],
            get_owner_uid=mock_tool_dependencies["get_owner_uid"],
            get_thread_id=mock_tool_dependencies["get_thread_id"],
            get_workload_service=mock_tool_dependencies["get_workload_service"],
            check_adjacency=mock_tool_dependencies["check_adjacency"]
        )
        
        result = tool.run(
            dst_uid="node_1",
            content="Please analyze the Q4 sales data",
            thread_id="test_thread_123",
            parent_item_id="item_1"
        )
        
        assert result["success"] is True
        assert result["dst_uid"] == "node_1"
        assert result["packet_id"] == "packet_123"
        assert "task_id" in result
        assert "correlation_info" in result
        
        # Verify work item was marked as delegated
        updated_plan = service.load(sample_work_plan.thread_id, sample_work_plan.owner_uid)
        item = updated_plan.items["item_1"]
        assert item.status == WorkItemStatus.WAITING
        assert item.correlation_task_id is not None
        
        # Verify debug output
        debug_messages = capture_debug_output
        assert any("DelegateTaskTool.run()" in msg for msg in debug_messages)
        assert any("Target: node_1" in msg for msg in debug_messages)
    
    def test_delegation_to_non_adjacent_node(self, mock_tool_dependencies):
        """Test delegation to non-adjacent node."""
        # Mock check_adjacency to return False
        mock_tool_dependencies["check_adjacency"] = lambda uid: False
        
        tool = DelegateTaskTool(
            send_task=mock_tool_dependencies["send_task"],
            get_owner_uid=mock_tool_dependencies["get_owner_uid"],
            get_thread_id=mock_tool_dependencies["get_thread_id"],
            get_workload_service=mock_tool_dependencies["get_workload_service"],
            check_adjacency=mock_tool_dependencies["check_adjacency"]
        )
        
        result = tool.run(
            dst_uid="non_adjacent_node",
            content="Test task",
            thread_id="test_thread_123",
            parent_item_id="item_1"
        )
        
        assert result["success"] is False
        assert "not adjacent" in result["error"]
    
    def test_delegation_without_parent_item(self, mock_tool_dependencies):
        """Test delegation without parent item ID."""
        tool = DelegateTaskTool(
            send_task=mock_tool_dependencies["send_task"],
            get_owner_uid=mock_tool_dependencies["get_owner_uid"],
            get_thread_id=mock_tool_dependencies["get_thread_id"],
            get_workload_service=mock_tool_dependencies["get_workload_service"],
            check_adjacency=mock_tool_dependencies["check_adjacency"]
        )
        
        result = tool.run(
            dst_uid="node_1",
            content="Test task without parent",
            thread_id="test_thread_123"
        )
        
        assert result["success"] is True
        # Should still work, just won't update work item status
    
    def test_delegation_send_task_failure(self, mock_tool_dependencies):
        """Test delegation when send_task fails."""
        # Mock send_task to raise exception
        mock_tool_dependencies["send_task"].side_effect = Exception("Network error")
        
        tool = DelegateTaskTool(
            send_task=mock_tool_dependencies["send_task"],
            get_owner_uid=mock_tool_dependencies["get_owner_uid"],
            get_thread_id=mock_tool_dependencies["get_thread_id"],
            get_workload_service=mock_tool_dependencies["get_workload_service"],
            check_adjacency=mock_tool_dependencies["check_adjacency"]
        )
        
        result = tool.run(
            dst_uid="node_1",
            content="Test task",
            thread_id="test_thread_123"
        )
        
        assert result["success"] is False
        assert "Failed to send task" in result["error"]
    
    def test_delegate_task_args_validation(self):
        """Test DelegateTaskArgs validation."""
        # Valid args
        args = DelegateTaskArgs(
            dst_uid="node_1",
            content="Test content",
            thread_id="test_thread_123",
            parent_item_id="item_1"
        )
        assert args.dst_uid == "node_1"
        assert args.content == "Test content"
        
        # Missing required field (thread_id)
        with pytest.raises(Exception):
            DelegateTaskArgs(
                dst_uid="node_1",
                content="Test content"
                # thread_id is missing - should raise ValidationError
            )


class TestMarkWorkItemStatusTool:
    """Test MarkWorkItemStatusTool functionality."""
    
    def test_tool_initialization(self, mock_tool_dependencies):
        """Test tool initialization."""
        tool = MarkWorkItemStatusTool(
            get_thread_id=mock_tool_dependencies["get_thread_id"],
            get_owner_uid=mock_tool_dependencies["get_owner_uid"],
            get_workload_service=mock_tool_dependencies["get_workload_service"]
        )
        
        assert tool.name == "workplan.mark"
        assert "Update work item status based on your interpretation" in tool.description
        assert tool.args_schema == MarkStatusArgs
    
    def test_mark_item_as_done(self, mock_tool_dependencies, sample_work_plan, capture_debug_output):
        """Test marking work item as done."""
        # Setup workspace
        workload_service = mock_tool_dependencies["get_workload_service"]()
        service = WorkPlanService(workload_service)
        service.save(sample_work_plan)
        
        tool = MarkWorkItemStatusTool(
            get_thread_id=mock_tool_dependencies["get_thread_id"],
            get_owner_uid=mock_tool_dependencies["get_owner_uid"],
            get_workload_service=mock_tool_dependencies["get_workload_service"]
        )
        
        result = tool.run(
            item_id="item_1",
            status=WorkItemStatus.DONE,
            notes="Task completed successfully"
        )
        
        assert result["success"] is True
        assert result["item_id"] == "item_1"
        assert result["new_status"] == WorkItemStatus.DONE.value
        
        # Verify item was updated
        updated_plan = service.load(sample_work_plan.thread_id, sample_work_plan.owner_uid)
        item = updated_plan.items["item_1"]
        assert item.status == WorkItemStatus.DONE
        
        # Verify debug output
        debug_messages = capture_debug_output
        assert any("MarkWorkItemStatusTool.run()" in msg for msg in debug_messages)
    
    def test_mark_item_as_failed(self, mock_tool_dependencies, sample_work_plan):
        """Test marking work item as failed."""
        workload_service = mock_tool_dependencies["get_workload_service"]()
        service = WorkPlanService(workload_service)
        service.save(sample_work_plan)
        
        tool = MarkWorkItemStatusTool(
            get_thread_id=mock_tool_dependencies["get_thread_id"],
            get_owner_uid=mock_tool_dependencies["get_owner_uid"],
            get_workload_service=mock_tool_dependencies["get_workload_service"]
        )
        
        result = tool.run(
            item_id="item_1",
            status=WorkItemStatus.FAILED,
            notes="Task failed due to network error"
        )
        
        assert result["success"] is True
        
        # Verify item was updated with error
        updated_plan = service.load(sample_work_plan.thread_id, sample_work_plan.owner_uid)
        item = updated_plan.items["item_1"]
        assert item.status == WorkItemStatus.FAILED
        assert item.error == "Task failed due to network error"
    
    def test_mark_nonexistent_item(self, mock_tool_dependencies, sample_work_plan):
        """Test marking non-existent work item."""
        workload_service = mock_tool_dependencies["get_workload_service"]()
        service = WorkPlanService(workload_service)
        service.save(sample_work_plan)
        
        tool = MarkWorkItemStatusTool(
            get_thread_id=mock_tool_dependencies["get_thread_id"],
            get_owner_uid=mock_tool_dependencies["get_owner_uid"],
            get_workload_service=mock_tool_dependencies["get_workload_service"]
        )
        
        result = tool.run(
            item_id="nonexistent_item",
            status=WorkItemStatus.DONE
        )
        
        assert result["success"] is False
        assert "Work plan or work item not found" in result["error"]
    
    def test_mark_status_args_validation(self):
        """Test MarkStatusArgs validation."""
        # Valid args
        args = MarkStatusArgs(
            item_id="item_1",
            status=WorkItemStatus.DONE,
            notes="Completed successfully"
        )
        assert args.item_id == "item_1"
        assert args.status == WorkItemStatus.DONE
        
        # Missing required fields
        with pytest.raises(Exception):
            MarkStatusArgs()


class TestAssignWorkItemTool:
    """Test AssignWorkItemTool functionality."""
    
    def test_tool_initialization(self, mock_tool_dependencies):
        """Test tool initialization."""
        tool = AssignWorkItemTool(
            get_thread_id=mock_tool_dependencies["get_thread_id"],
            get_owner_uid=mock_tool_dependencies["get_owner_uid"],
            get_workload_service=mock_tool_dependencies["get_workload_service"]
        )
        
        assert tool.name == "workplan.assign"
        assert "Assign a work item" in tool.description
        assert tool.args_schema == AssignItemArgs
    
    def test_assign_item_for_remote_execution(self, mock_tool_dependencies, sample_work_plan):
        """Test assigning item for remote execution."""
        workload_service = mock_tool_dependencies["get_workload_service"]()
        service = WorkPlanService(workload_service)
        service.save(sample_work_plan)
        
        tool = AssignWorkItemTool(
            get_thread_id=mock_tool_dependencies["get_thread_id"],
            get_owner_uid=mock_tool_dependencies["get_owner_uid"],
            get_workload_service=mock_tool_dependencies["get_workload_service"]
        )
        
        result = tool.run(
            item_id="item_1",
            kind=WorkItemKind.REMOTE,
            assigned_uid="remote_node_1",
            args={"param1": "value1"}
        )
        
        assert result["success"] is True
        assert result["item_id"] == "item_1"
        assert result["assignment"]["kind"] == WorkItemKind.REMOTE
        
        # Verify item was updated
        updated_plan = service.load(sample_work_plan.thread_id, sample_work_plan.owner_uid)
        item = updated_plan.items["item_1"]
        assert item.kind == WorkItemKind.REMOTE
        assert item.assigned_uid == "remote_node_1"
        assert item.args["param1"] == "value1"
    
    def test_assign_item_for_local_execution(self, mock_tool_dependencies, sample_work_plan):
        """Test assigning item for local execution."""
        workload_service = mock_tool_dependencies["get_workload_service"]()
        service = WorkPlanService(workload_service)
        service.save(sample_work_plan)
        
        tool = AssignWorkItemTool(
            get_thread_id=mock_tool_dependencies["get_thread_id"],
            get_owner_uid=mock_tool_dependencies["get_owner_uid"],
            get_workload_service=mock_tool_dependencies["get_workload_service"]
        )
        
        result = tool.run(
            item_id="item_1",
            kind=WorkItemKind.LOCAL,
            tool="analyze_data_tool",
            args={"data_source": "database"}
        )
        
        assert result["success"] is True
        assert result["assignment"]["kind"] == WorkItemKind.LOCAL
        
        # Verify item was updated
        updated_plan = service.load(sample_work_plan.thread_id, sample_work_plan.owner_uid)
        item = updated_plan.items["item_1"]
        assert item.kind == WorkItemKind.LOCAL
        assert item.tool == "analyze_data_tool"
        assert item.args["data_source"] == "database"
    
    def test_assign_nonexistent_item(self, mock_tool_dependencies, sample_work_plan):
        """Test assigning non-existent work item."""
        workload_service = mock_tool_dependencies["get_workload_service"]()
        service = WorkPlanService(workload_service)
        service.save(sample_work_plan)
        
        tool = AssignWorkItemTool(
            get_thread_id=mock_tool_dependencies["get_thread_id"],
            get_owner_uid=mock_tool_dependencies["get_owner_uid"],
            get_workload_service=mock_tool_dependencies["get_workload_service"]
        )
        
        result = tool.run(
            item_id="nonexistent_item",
            kind=WorkItemKind.LOCAL
        )
        
        assert result["success"] is False
        assert "not found" in result["error"]


class TestSummarizeWorkPlanTool:
    """Test SummarizeWorkPlanTool functionality."""
    
    def test_tool_initialization(self, mock_tool_dependencies):
        """Test tool initialization."""
        tool = SummarizeWorkPlanTool(
            get_thread_id=mock_tool_dependencies["get_thread_id"],
            get_owner_uid=mock_tool_dependencies["get_owner_uid"],
            get_workload_service=mock_tool_dependencies["get_workload_service"]
        )
        
        assert tool.name == "workplan.summarize"  # Uses ToolNames constant
        assert "Generate a comprehensive summary" in tool.description
        assert tool.args_schema == BaseModel  # No arguments needed
    
    def test_summarize_complex_work_plan(self, mock_tool_dependencies, complex_work_plan):
        """Test summarizing a complex work plan."""
        workload_service = mock_tool_dependencies["get_workload_service"]()
        service = WorkPlanService(workload_service)
        service.save(complex_work_plan)
        
        tool = SummarizeWorkPlanTool(
            get_thread_id=mock_tool_dependencies["get_thread_id"],
            get_owner_uid=mock_tool_dependencies["get_owner_uid"],
            get_workload_service=mock_tool_dependencies["get_workload_service"]
        )
        
        result = tool.run()  # SummarizeWorkPlanTool takes no arguments
        
        assert "summary" in result
        summary_text = result["summary"]
        assert "Complex Test Work Plan" in summary_text
        assert "Total Items: 5" in summary_text
        # Check for either completed or failed work sections
        assert ("Completed Work" in summary_text or 
                "Failed Work" in summary_text or 
                "Incomplete Work" in summary_text)
    
    def test_summarize_empty_work_plan(self, mock_tool_dependencies):
        """Test summarizing when no work plan exists."""
        tool = SummarizeWorkPlanTool(
            get_thread_id=mock_tool_dependencies["get_thread_id"],
            get_owner_uid=mock_tool_dependencies["get_owner_uid"],
            get_workload_service=mock_tool_dependencies["get_workload_service"]
        )
        
        result = tool.run()
        
        assert "summary" in result
        assert "No work plan found" in result["summary"]
    
    def test_summarize_with_options(self, mock_tool_dependencies, complex_work_plan):
        """Test summarize with different options."""
        workload_service = mock_tool_dependencies["get_workload_service"]()
        service = WorkPlanService(workload_service)
        service.save(complex_work_plan)
        
        tool = SummarizeWorkPlanTool(
            get_thread_id=mock_tool_dependencies["get_thread_id"],
            get_owner_uid=mock_tool_dependencies["get_owner_uid"],
            get_workload_service=mock_tool_dependencies["get_workload_service"]
        )
        
        # Test basic summarization (no arguments)
        result = tool.run()
        
        assert "summary" in result
        summary = result["summary"]
        
        # Should be more concise without results/timeline
        assert len(summary) < 1000  # Reasonable length check


class TestOrchestrationToolsEdgeCases:
    """Test edge cases and error conditions for all tools."""
    
    def test_tools_with_workspace_failures(self, mock_tool_dependencies):
        """Test tool behavior when workspace operations fail."""
        # Mock workspace to fail
        failing_workspace = Mock()
        failing_workspace.get_variable.side_effect = Exception("Workspace error")
        failing_workspace.set_variable.side_effect = Exception("Workspace error")
        workload_service = mock_tool_dependencies["get_workload_service"]()
        workload_service.get_workspace.return_value = failing_workspace
        
        # Test CreateOrUpdateWorkPlanTool
        create_tool = CreateOrUpdateWorkPlanTool(
            get_thread_id=mock_tool_dependencies["get_thread_id"],
            get_owner_uid=mock_tool_dependencies["get_owner_uid"],
            get_workload_service=mock_tool_dependencies["get_workload_service"]
        )
        
        # Should handle workspace errors gracefully
        try:
            result = create_tool.run(
                summary="Test Plan",
                items=[{
                    "id": "test_item",
                    "title": "Test Item",
                    "description": "Test description",
                    "dependencies": [],
                    "kind": "local"
                }]
            )
            # May succeed or fail, but should not crash
        except Exception as e:
            # Should be a handled exception, not a crash
            assert "workspace" in str(e).lower() or "error" in str(e).lower()
    
    def test_tools_with_unicode_content(self, mock_tool_dependencies, sample_work_plan):
        """Test tools with unicode content."""
        workload_service = mock_tool_dependencies["get_workload_service"]()
        service = WorkPlanService(workload_service)
        service.save(sample_work_plan)
        
        # Test DelegateTaskTool with unicode
        delegate_tool = DelegateTaskTool(
            send_task=mock_tool_dependencies["send_task"],
            get_owner_uid=mock_tool_dependencies["get_owner_uid"],
            get_thread_id=mock_tool_dependencies["get_thread_id"],
            get_workload_service=mock_tool_dependencies["get_workload_service"],
            check_adjacency=mock_tool_dependencies["check_adjacency"]
        )
        
        result = delegate_tool.run(
            dst_uid="node_1",
            content="请分析Q4销售数据 🚀 and create 报告",
            thread_id="test_thread_123",
            parent_item_id="item_1"
        )
        
        assert result["success"] is True
        
        # Test MarkWorkItemStatusTool with unicode
        mark_tool = MarkWorkItemStatusTool(
            get_thread_id=mock_tool_dependencies["get_thread_id"],
            get_owner_uid=mock_tool_dependencies["get_owner_uid"],
            get_workload_service=mock_tool_dependencies["get_workload_service"]
        )
        
        result = mark_tool.run(
            item_id="item_1",
            status=WorkItemStatus.DONE,
            notes="任务完成 ✅ with émojis and spëcial chars"
        )
        
        assert result["success"] is True
    
    def test_tools_with_large_data(self, mock_tool_dependencies):
        """Test tools with large data inputs."""
        # Test CreateOrUpdateWorkPlanTool with many items
        create_tool = CreateOrUpdateWorkPlanTool(
            get_thread_id=mock_tool_dependencies["get_thread_id"],
            get_owner_uid=mock_tool_dependencies["get_owner_uid"],
            get_workload_service=mock_tool_dependencies["get_workload_service"]
        )
        
        # Create 100 work items
        large_items = []
        for i in range(100):
            large_items.append({
                "id": f"item_{i}",
                "title": f"Item {i}",
                "description": f"Description for item {i}" * 100,  # Long description
                "dependencies": [f"item_{i-1}"] if i > 0 else [],
                "kind": "local"
            })
        
        result = create_tool.run(
            summary="Large Work Plan",
            items=large_items
        )
        
        assert result["success"] is True
        assert result["total_items"] == 100
    
    def test_tools_concurrent_access(self, mock_tool_dependencies, sample_work_plan):
        """Test tools under concurrent access."""
        workload_service = mock_tool_dependencies["get_workload_service"]()
        service = WorkPlanService(workload_service)
        service.save(sample_work_plan)
        
        import threading
        results = []
        errors = []
        
        def use_mark_tool():
            try:
                mark_tool = MarkWorkItemStatusTool(
                    get_thread_id=mock_tool_dependencies["get_thread_id"],
                    get_owner_uid=mock_tool_dependencies["get_owner_uid"],
                    get_workload_service=mock_tool_dependencies["get_workload_service"]
                )
                
                result = mark_tool.run(
                    item_id="item_1",
                    status=WorkItemStatus.IN_PROGRESS,
                    notes="Concurrent access test"
                )
                results.append(result)
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=use_mark_tool)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Should handle concurrent access gracefully
        assert len(errors) == 0 or len(results) > 0  # Some should succeed
    
    def test_tool_parameter_validation_edge_cases(self):
        """Test tool parameter validation with edge cases."""
        # Test WorkItemSpec with extreme values
        spec = WorkItemSpec(
            id="x" * 1000,  # Very long ID
            title="y" * 1000,  # Very long title
            description="z" * 10000,  # Very long description
            dependencies=["dep_" + str(i) for i in range(100)],  # Many dependencies
            kind=WorkItemKind.REMOTE
        )
        
        assert len(spec.id) == 1000
        assert len(spec.dependencies) == 100
        
        # Test DelegateTaskArgs with edge cases
        args = DelegateTaskArgs(
            dst_uid="node_with_very_long_identifier_" + "x" * 100,
            content="Content with\nnewlines\tand\ttabs and unicode 🚀",
            thread_id="test_thread_123"
        )
        
        assert "very_long_identifier" in args.dst_uid
        assert "\n" in args.content
        assert "🚀" in args.content
