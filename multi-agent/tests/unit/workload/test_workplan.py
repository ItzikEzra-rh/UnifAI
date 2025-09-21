"""
Unit tests for WorkPlan and WorkPlanService.

Tests the core functionality of work planning without external dependencies.
"""

import pytest
from datetime import datetime
from elements.nodes.common.workload import (
    WorkPlan, WorkItem, WorkItemStatus, WorkItemKind, WorkPlanService,
    ToolArguments, WorkItemResult, WorkItemStatusCounts, WorkPlanStatusSummary,
    Workspace, WorkspaceContext, AgentResult
)


class TestWorkItem:
    """Test WorkItem model functionality."""
    
    def test_create_work_item(self):
        """Test creating a basic work item."""
        item = WorkItem(
            id="test_task_1",
            title="Test Task",
            description="A test work item"
        )
        
        assert item.title == "Test Task"
        assert item.description == "A test work item"
        assert item.kind == WorkItemKind.LOCAL  # Updated to use enum
        assert item.status == WorkItemStatus.PENDING
        assert item.dependencies == []  # Updated field name
        assert item.id == "test_task_1"
    
    def test_work_item_dependencies(self):
        """Test work item with dependencies."""
        item1 = WorkItem(id="task_1", title="Task 1")
        item2 = WorkItem(
            id="task_2",
            title="Task 2",
            dependencies=[item1.id]  # Updated field name
        )
        
        # Test dependency check with new method names
        assert item1.is_ready_for_execution(set())
        assert not item2.is_ready_for_execution(set())
        assert item2.is_ready_for_execution({item1.id})
        
        # Test blocking check
        assert not item1.is_blocked(set())
        assert item2.is_blocked(set())
        assert not item2.is_blocked({item1.id})
    
    def test_update_status(self):
        """Test updating work item status."""
        item = WorkItem(id="test", title="Test")
        original_time = item.updated_at
        
        # Pydantic models are immutable, so we test direct assignment
        item.status = WorkItemStatus.IN_PROGRESS
        
        assert item.status == WorkItemStatus.IN_PROGRESS
        # Note: updated_at is not automatically updated in Pydantic models
        # This would be handled by the service layer


class TestWorkPlan:
    """Test WorkPlan model functionality."""
    
    def test_create_work_plan(self):
        """Test creating a work plan."""
        plan = WorkPlan(
            summary="Test plan",
            thread_id="thread-123",
            owner_uid="node-1"
        )
        
        assert plan.thread_id == "thread-123"
        assert plan.owner_uid == "node-1"
        assert plan.summary == "Test plan"
        assert len(plan.items) == 0
    
    def test_add_items(self):
        """Test adding items to plan."""
        plan = WorkPlan(summary="Test", thread_id="t1", owner_uid="n1")
        
        item1 = WorkItem(id="task1", title="Task 1")
        item2 = WorkItem(id="task2", title="Task 2")
        
        # Pydantic models use direct assignment to items dict
        plan.items[item1.id] = item1
        plan.items[item2.id] = item2
        
        assert len(plan.items) == 2
        assert item1.id in plan.items
        assert item2.id in plan.items
    
    def test_get_ready_items(self):
        """Test getting ready items with dependencies."""
        plan = WorkPlan(summary="Test", thread_id="t1", owner_uid="n1")
        
        # Create items with dependencies
        item1 = WorkItem(id="task1", title="Task 1")
        item2 = WorkItem(id="task2", title="Task 2", dependencies=[item1.id])
        item3 = WorkItem(id="task3", title="Task 3", dependencies=[item2.id])
        
        plan.items[item1.id] = item1
        plan.items[item2.id] = item2
        plan.items[item3.id] = item3
        
        # Initially only item1 is ready
        ready = plan.get_ready_items()
        assert len(ready) == 1
        assert ready[0].id == item1.id
        
        # Mark item1 as done
        item1.status = WorkItemStatus.DONE
        plan.items[item1.id] = item1
        
        # Now item2 should be ready
        ready = plan.get_ready_items()
        assert len(ready) == 1
        assert ready[0].id == item2.id
    
    def test_status_counts(self):
        """Test getting status counts."""
        plan = WorkPlan(summary="Test", thread_id="t1", owner_uid="n1")
        
        # Add items with different statuses
        item1 = WorkItem(id="task1", title="Task 1")
        item2 = WorkItem(id="task2", title="Task 2")
        item3 = WorkItem(id="task3", title="Task 3", status=WorkItemStatus.DONE)
        
        plan.items[item1.id] = item1
        plan.items[item2.id] = item2
        plan.items[item3.id] = item3
        
        counts = plan.get_status_counts()
        assert counts.pending == 2  # Now returns WorkItemStatusCounts model
        assert counts.done == 1
        assert counts.failed == 0
    
    def test_is_complete(self):
        """Test completion check."""
        plan = WorkPlan(summary="Test", thread_id="t1", owner_uid="n1")
        
        item1 = WorkItem(id="task1", title="Task 1")
        item2 = WorkItem(id="task2", title="Task 2")
        
        plan.items[item1.id] = item1
        plan.items[item2.id] = item2
        
        assert not plan.is_complete()
        
        # Update item1 status
        item1.status = WorkItemStatus.DONE
        plan.items[item1.id] = item1
        assert not plan.is_complete()
        
        # Update item2 status
        item2.status = WorkItemStatus.FAILED
        plan.items[item2.id] = item2
        assert plan.is_complete()  # All items done or failed


class TestWorkPlanService:
    """Test WorkPlanService functionality."""
    
    @pytest.fixture
    def workspace(self):
        """Create a test workspace."""
        return Workspace(
            thread_id="test-thread",
            context=WorkspaceContext()
        )
    
    def test_create_and_load_plan(self, workspace):
        """Test creating and loading a plan."""
        service = WorkPlanService(workspace)
        
        # Create plan
        plan = service.create(
            thread_id="test-thread",
            owner_uid="node-1",
            created_by="user-1"
        )
        
        assert plan.thread_id == "test-thread"
        assert plan.owner_uid == "node-1"
        
        # Load plan
        loaded = service.load("node-1")
        assert loaded is not None
        assert loaded.thread_id == plan.thread_id
    
    def test_add_items_to_plan(self, workspace):
        """Test adding items via service."""
        service = WorkPlanService(workspace)
        
        # Create plan
        service.create("test-thread", "node-1", "user-1")
        
        # Add items
        items = [
            WorkItem(title="Task 1"),
            WorkItem(title="Task 2")
        ]
        
        success = service.add_items("node-1", items)
        assert success
        
        # Verify items added
        plan = service.load("node-1")
        assert len(plan.items) == 2
    
    def test_update_item_status(self, workspace):
        """Test updating item status."""
        service = WorkPlanService(workspace)
        
        # Create plan with item
        plan = service.create("test-thread", "node-1", "user-1")
        item = WorkItem(title="Test Task")
        plan.add_item(item)
        service.save(plan)
        
        # Update status
        success = service.update_item_status(
            owner_uid="node-1",
            item_id=item.id,
            status=WorkItemStatus.IN_PROGRESS
        )
        
        assert success
        
        # Verify update
        plan = service.load("node-1")
        assert plan.items[item.id].status == WorkItemStatus.IN_PROGRESS
    
    def test_ingest_task_response(self, workspace):
        """Test ingesting task responses."""
        service = WorkPlanService(workspace)
        
        # Create plan with remote item
        plan = service.create("test-thread", "node-1", "user-1")
        item = WorkItem(
            title="Remote Task",
            kind="remote",
            assigned_uid="node-2",
            correlation_task_id="task-123"
        )
        plan.add_item(item)
        service.save(plan)
        
        # Create result
        result = AgentResult(
            content="Task completed",
            agent_id="node-2",
            agent_name="Worker Node"
        )
        
        # Ingest response
        success = service.ingest_task_response(
            owner_uid="node-1",
            correlation_task_id="task-123",
            result=result
        )
        
        assert success
        
        # Verify item updated
        plan = service.load("node-1")
        updated_item = plan.items[item.id]
        assert updated_item.status == WorkItemStatus.DONE
        assert updated_item.result_ref is not None
        assert "agent_result" in updated_item.result_ref["type"]
    
    def test_namespaced_plans(self, workspace):
        """Test that plans are namespaced by owner."""
        service = WorkPlanService(workspace)
        
        # Create plans for different owners
        plan1 = service.create("test-thread", "node-1", "user-1")
        plan2 = service.create("test-thread", "node-2", "user-1")
        
        # Add different items
        item1 = WorkItem(title="Node 1 Task")
        plan1.add_item(item1)
        service.save(plan1)
        
        item2 = WorkItem(title="Node 2 Task")
        plan2.add_item(item2)
        service.save(plan2)
        
        # Verify isolation
        loaded1 = service.load("node-1")
        loaded2 = service.load("node-2")
        
        assert len(loaded1.items) == 1
        assert "Node 1 Task" in loaded1.items[item1.id].title
        
        assert len(loaded2.items) == 1
        assert "Node 2 Task" in loaded2.items[item2.id].title


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

