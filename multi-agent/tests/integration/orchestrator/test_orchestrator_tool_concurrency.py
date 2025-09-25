"""
Integration tests for orchestrator tool concurrency.

Tests that the orchestrator's workplan tools can be called concurrently
without race conditions, simulating real LLM multi-tool calls.
"""

import pytest
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import Mock

from elements.nodes.common.workload import (
    WorkPlanService, WorkPlan, WorkItem, WorkItemStatus, WorkItemKind
)
from elements.nodes.common.workload.in_memory_service import InMemoryWorkloadService
from elements.tools.builtin.workplan.assign_item import AssignWorkItemTool
from elements.tools.builtin.workplan.mark_status import MarkWorkItemStatusTool
from elements.tools.builtin.workplan.create_or_update import CreateOrUpdateWorkPlanTool


class TestOrchestratorToolConcurrency:
    """Test concurrent execution of orchestrator tools."""
    
    @pytest.fixture
    def workload_service(self):
        """Create in-memory workload service for testing."""
        return InMemoryWorkloadService()
    
    @pytest.fixture
    def orchestrator_tools(self, workload_service):
        """Create orchestrator tools for testing."""
        thread_id = "test_thread"
        owner_uid = "orchestrator_001"
        
        # Create thread and initial workspace
        workload_service.create_thread("Test Thread", "Test concurrent tool calls", owner_uid)
        
        # Tool accessors
        def get_thread_id():
            return thread_id
        
        def get_owner_uid():
            return owner_uid
        
        def get_workload_service():
            return workload_service
        
        # Create tools
        assign_tool = AssignWorkItemTool(get_thread_id, get_owner_uid, get_workload_service)
        mark_tool = MarkWorkItemStatusTool(get_thread_id, get_owner_uid, get_workload_service)
        create_tool = CreateOrUpdateWorkPlanTool(get_thread_id, get_owner_uid, get_workload_service)
        
        return {
            'assign': assign_tool,
            'mark': mark_tool,
            'create': create_tool,
            'thread_id': thread_id,
            'owner_uid': owner_uid,
            'service': WorkPlanService(workload_service)
        }
    
    def test_concurrent_tool_calls_allocation_phase(self, orchestrator_tools):
        """Test concurrent tool calls simulating allocation phase."""
        tools = orchestrator_tools
        
        # Create initial plan using CreateOrUpdateWorkPlanTool
        create_result = tools['create'].run(
            summary="Allocation Phase Test Plan",
            items=[
                {
                    "id": "task_1",
                    "title": "Analyze data",
                    "description": "Analyze the provided dataset",
                    "dependencies": [],
                    "kind": "local"
                },
                {
                    "id": "task_2", 
                    "title": "Generate report",
                    "description": "Generate analysis report",
                    "dependencies": ["task_1"],
                    "kind": "local"
                },
                {
                    "id": "task_3",
                    "title": "Validate results",
                    "description": "Validate analysis results",
                    "dependencies": [],
                    "kind": "local"
                },
                {
                    "id": "task_4",
                    "title": "Send notification",
                    "description": "Send completion notification",
                    "dependencies": ["task_2", "task_3"],
                    "kind": "local"
                }
            ]
        )
        
        assert create_result["success"] is True
        
        # Simulate LLM making concurrent tool calls in allocation phase
        results = []
        results_lock = threading.Lock()
        
        def assign_task_1():
            """Assign task_1 to remote execution."""
            result = tools['assign'].run(
                item_id="task_1",
                kind="remote",
                assigned_uid="data_analyzer_node"
            )
            with results_lock:
                results.append(("assign_task_1", result))
        
        def assign_task_3():
            """Assign task_3 to remote execution."""
            result = tools['assign'].run(
                item_id="task_3",
                kind="remote", 
                assigned_uid="validator_node"
            )
            with results_lock:
                results.append(("assign_task_3", result))
        
        def assign_task_2():
            """Assign task_2 to local execution."""
            result = tools['assign'].run(
                item_id="task_2",
                kind="local"
            )
            with results_lock:
                results.append(("assign_task_2", result))
        
        def update_plan():
            """Add another task to the plan concurrently."""
            result = tools['create'].run(
                summary="Updated Allocation Phase Test Plan",
                items=[
                    {
                        "id": "task_5",
                        "title": "Archive results",
                        "description": "Archive the final results",
                        "dependencies": ["task_4"],
                        "kind": "local"
                    }
                ]
            )
            with results_lock:
                results.append(("update_plan", result))
        
        # Execute concurrent tool calls
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [
                executor.submit(assign_task_1),
                executor.submit(assign_task_3),
                executor.submit(assign_task_2),
                executor.submit(update_plan)
            ]
            
            for future in as_completed(futures):
                future.result()  # Wait for completion
        
        # Verify all operations succeeded
        assert len(results) == 4
        for operation, result in results:
            assert result["success"] is True, f"Operation {operation} failed: {result}"
        
        # Verify final plan state
        final_plan = tools['service'].load(tools['thread_id'], tools['owner_uid'])
        assert final_plan is not None
        assert len(final_plan.items) == 5  # Original 4 + 1 new
        
        # Verify assignments
        assert final_plan.items["task_1"].kind == WorkItemKind.REMOTE
        assert final_plan.items["task_1"].assigned_uid == "data_analyzer_node"
        
        assert final_plan.items["task_3"].kind == WorkItemKind.REMOTE
        assert final_plan.items["task_3"].assigned_uid == "validator_node"
        
        assert final_plan.items["task_2"].kind == WorkItemKind.LOCAL
        assert final_plan.items["task_2"].assigned_uid is None
        
        # Verify new task was added
        assert "task_5" in final_plan.items
        assert final_plan.items["task_5"].dependencies == ["task_4"]
    
    def test_concurrent_tool_calls_monitoring_phase(self, orchestrator_tools):
        """Test concurrent tool calls simulating monitoring phase."""
        tools = orchestrator_tools
        
        # Create plan with items in waiting status
        service = tools['service']
        plan = service.create(tools['thread_id'], tools['owner_uid'])
        plan.summary = "Monitoring Phase Test Plan"
        
        # Add items with different statuses
        for i in range(5):
            item = WorkItem(
                id=f"item_{i}",
                title=f"Task {i}",
                description=f"Description for task {i}",
                status=WorkItemStatus.WAITING,
                kind=WorkItemKind.REMOTE,
                assigned_uid=f"node_{i}",
                correlation_task_id=f"task_{i}_correlation"
            )
            plan.items[item.id] = item
        
        service.save(plan)
        
        # Simulate concurrent status updates during monitoring
        results = []
        results_lock = threading.Lock()
        
        def mark_item_done(item_id):
            """Mark item as done."""
            result = tools['mark'].run(
                item_id=item_id,
                status="done",
                notes=f"Successfully completed {item_id}"
            )
            with results_lock:
                results.append((f"done_{item_id}", result))
        
        def mark_item_failed(item_id):
            """Mark item as failed."""
            result = tools['mark'].run(
                item_id=item_id,
                status="failed",
                notes=f"Failed to complete {item_id} due to timeout"
            )
            with results_lock:
                results.append((f"failed_{item_id}", result))
        
        def mark_item_in_progress(item_id):
            """Mark item as in progress."""
            result = tools['mark'].run(
                item_id=item_id,
                status="in_progress",
                notes=f"Started processing {item_id}"
            )
            with results_lock:
                results.append((f"progress_{item_id}", result))
        
        # Execute concurrent status updates
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(mark_item_done, "item_0"),
                executor.submit(mark_item_done, "item_1"),
                executor.submit(mark_item_failed, "item_2"),
                executor.submit(mark_item_in_progress, "item_3"),
                executor.submit(mark_item_in_progress, "item_4")
            ]
            
            for future in as_completed(futures):
                future.result()
        
        # Verify all operations succeeded
        assert len(results) == 5
        for operation, result in results:
            assert result["success"] is True, f"Operation {operation} failed: {result}"
        
        # Verify final statuses
        final_plan = service.load(tools['thread_id'], tools['owner_uid'])
        assert final_plan.items["item_0"].status == WorkItemStatus.DONE
        assert final_plan.items["item_1"].status == WorkItemStatus.DONE
        assert final_plan.items["item_2"].status == WorkItemStatus.FAILED
        assert final_plan.items["item_3"].status == WorkItemStatus.IN_PROGRESS
        assert final_plan.items["item_4"].status == WorkItemStatus.IN_PROGRESS
        
        # Verify notes were set correctly (only FAILED status stores notes in error field)
        assert final_plan.items["item_0"].error is None  # DONE status doesn't store notes
        assert final_plan.items["item_1"].error is None  # DONE status doesn't store notes  
        assert "Failed to complete item_2" in final_plan.items["item_2"].error  # FAILED status stores notes
    
    def test_mixed_tool_calls_high_contention(self, orchestrator_tools):
        """Test mixed tool calls with high contention on same work items."""
        tools = orchestrator_tools
        
        # Create plan with fewer items but more contention
        service = tools['service']
        plan = service.create(tools['thread_id'], tools['owner_uid'])
        plan.summary = "High Contention Test Plan"
        
        # Add only 3 items that will be modified concurrently
        for i in range(3):
            item = WorkItem(
                id=f"contested_item_{i}",
                title=f"Contested Task {i}",
                description=f"Task {i} with high contention",
                kind=WorkItemKind.LOCAL
            )
            plan.items[item.id] = item
        
        service.save(plan)
        
        # Track all operations
        operations = []
        ops_lock = threading.Lock()
        
        def rapid_assign_worker(worker_id):
            """Worker that rapidly assigns items."""
            for i in range(3):
                item_id = f"contested_item_{i}"
                result = tools['assign'].run(
                    item_id=item_id,
                    kind="remote",
                    assigned_uid=f"rapid_worker_{worker_id}"
                )
                with ops_lock:
                    operations.append((f"assign_{worker_id}_{i}", result["success"]))
                
                # Small delay to create more contention
                time.sleep(0.001)
        
        def rapid_status_worker(worker_id):
            """Worker that rapidly updates status."""
            for i in range(3):
                item_id = f"contested_item_{i}"
                result = tools['mark'].run(
                    item_id=item_id,
                    status="in_progress",
                    notes=f"Updated by status worker {worker_id}"
                )
                with ops_lock:
                    operations.append((f"status_{worker_id}_{i}", result["success"]))
                
                time.sleep(0.001)
        
        # Run high-contention operations
        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = []
            
            # 3 assign workers competing for same items
            for i in range(3):
                futures.append(executor.submit(rapid_assign_worker, i))
            
            # 3 status workers competing for same items
            for i in range(3):
                futures.append(executor.submit(rapid_status_worker, i))
            
            for future in as_completed(futures):
                future.result()
        
        # Verify operations completed (some may have failed due to timing, but no data corruption)
        successful_ops = [op for op, success in operations if success]
        assert len(successful_ops) > 0  # At least some operations should succeed
        
        # Most importantly, verify data integrity (no corruption)
        final_plan = service.load(tools['thread_id'], tools['owner_uid'])
        assert final_plan is not None
        assert len(final_plan.items) == 3  # No items lost
        
        # All items should still have valid data
        for item in final_plan.items.values():
            assert item.id.startswith("contested_item_")
            assert item.title.startswith("Contested Task")
            # assigned_uid should be valid if set
            if item.assigned_uid:
                assert item.assigned_uid.startswith("rapid_worker_")
        
        print(f"Completed {len(successful_ops)} successful operations out of {len(operations)} total")
        print(f"Final plan has {len(final_plan.items)} items with no corruption")
    
    def test_tool_atomicity_vs_old_race_condition(self, orchestrator_tools):
        """Test that demonstrates old race condition is fixed by new atomic operations."""
        tools = orchestrator_tools
        service = tools['service']
        
        # Create a plan with one item to maximize contention
        plan = service.create(tools['thread_id'], tools['owner_uid'])
        plan.items["critical_item"] = WorkItem(
            id="critical_item",
            title="Critical Task",
            description="Task that tests atomicity",
            kind=WorkItemKind.LOCAL
        )
        service.save(plan)
        
        # Track assignment results
        assignment_results = []
        results_lock = threading.Lock()
        
        def competing_assigner(worker_id):
            """Worker that competes to assign the same item."""
            result = tools['assign'].run(
                item_id="critical_item",
                kind="remote",
                assigned_uid=f"competing_node_{worker_id}"
            )
            
            with results_lock:
                assignment_results.append((worker_id, result["success"]))
        
        # Run 10 competing assigners simultaneously
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(competing_assigner, i) for i in range(10)]
            for future in as_completed(futures):
                future.result()
        
        # All operations should succeed due to atomic operations
        successful_assignments = [r for w, r in assignment_results if r]
        assert len(successful_assignments) == 10  # All should succeed
        
        # Final state should be consistent (last assignment wins)
        final_plan = service.load(tools['thread_id'], tools['owner_uid'])
        final_item = final_plan.items["critical_item"]
        
        # Item should have been assigned to one of the competing nodes
        assert final_item.kind == WorkItemKind.REMOTE
        assert final_item.assigned_uid.startswith("competing_node_")
        
        # Most importantly: no data corruption or lost updates
        assert final_item.id == "critical_item"
        assert final_item.title == "Critical Task"
        assert final_item.description == "Task that tests atomicity"
