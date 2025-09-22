"""
Performance Integration Tests for Orchestrator System.

These tests verify orchestrator performance characteristics under various
load conditions and operational scenarios. They ensure the system maintains
acceptable performance levels and resource utilization.

SOLID Principles Applied:
- Single Responsibility: Each test focuses on one performance aspect
- Open/Closed: Tests are extensible for new performance scenarios
- Liskov Substitution: Uses real components with performance monitoring
- Interface Segregation: Clean performance testing interfaces
- Dependency Inversion: Depends on performance abstractions and metrics
"""

import pytest
from unittest.mock import patch, Mock
from typing import Dict, Any, List
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from elements.nodes.orchestrator.orchestrator_node import OrchestratorNode
from elements.nodes.common.workload import Task, WorkPlan, WorkPlanService
from elements.llms.common.chat.message import ChatMessage, Role
from core.models import ElementCard

# Import our clean, SOLID fixtures
from tests.fixtures.orchestrator_integration import (
    PredictableLLM, ExecutionTracker
)


@pytest.mark.integration
@pytest.mark.orchestrator
@pytest.mark.performance
class TestOrchestratorPerformanceIntegration:
    """
    Performance integration tests for orchestrator system.
    
    These tests verify that the orchestrator maintains acceptable performance
    characteristics under various operational conditions and load patterns.
    """
    
    def test_single_task_processing_performance_acceptable(
        self,
        integration_orchestrator: OrchestratorNode,
        predictable_llm: PredictableLLM,
        integration_task_factory,
        execution_tracker: ExecutionTracker
    ):
        """
        Test single task processing performance baseline.
        
        Verifies:
        1. Single task processing time
        2. Memory usage stability  
        3. Response time consistency
        4. Baseline performance metrics
        """
        try:
            # Create standard task for performance baseline
            task = integration_task_factory(
                content="Generate standard performance analysis report",
                thread_id="performance_baseline_thread"
            )
            
            # Set up predictable response for consistent timing
            predictable_llm.add_tool_call_response(
                tool_name="workplan.create_or_update",
                arguments={
                    "summary": "Performance baseline work plan",
                    "items": [{
                        "id": "baseline_task",
                        "title": "Baseline Performance Task",
                        "description": "Standard task for performance measurement",
                        "kind": "local",
                        "dependencies": []
                    }]
                },
                content="Created baseline performance plan"
            )
            
            # Create IEM packet
            from core.iem.packets import TaskPacket
            from core.iem.models import ElementAddress
            
            task_packet = TaskPacket.create(
                src=ElementAddress(uid="user"),
                dst=ElementAddress(uid=integration_orchestrator.uid),
                task=task
            )
            
            integration_orchestrator._state.inter_packets.append(task_packet)
            
            # Measure performance
            start_time = time.time()
            start_memory = self._get_memory_usage()
            
            with patch.object(integration_orchestrator, 'get_adjacent_nodes', return_value={}), \
                 patch.object(integration_orchestrator, 'send_task', return_value="performance_task"):
                
                result = integration_orchestrator.run(integration_orchestrator._state)
                execution_tracker.track_llm_call()
                
                end_time = time.time()
                end_memory = self._get_memory_usage()
                
                execution_time = end_time - start_time
                memory_delta = end_memory - start_memory
                
                # VERIFY: Performance within acceptable bounds
                assert result is not None
                assert execution_time < 5.0, f"Single task took too long: {execution_time:.2f}s"
                assert memory_delta < 50 * 1024 * 1024, f"Memory usage too high: {memory_delta / 1024 / 1024:.1f}MB"  # 50MB limit
                
                # VERIFY: Execution completed successfully
                assert predictable_llm.call_count > 0
                
                print(f"✅ SINGLE TASK PERFORMANCE: {execution_time:.3f}s, Memory: {memory_delta / 1024 / 1024:.1f}MB")
                
        except Exception as e:
            execution_tracker.track_error(str(e))
            pytest.fail(f"Single task performance test failed: {e}")
    
    def test_multiple_sequential_tasks_performance_acceptable(
        self,
        integration_orchestrator: OrchestratorNode,
        predictable_llm: PredictableLLM,
        integration_task_factory,
        execution_tracker: ExecutionTracker
    ):
        """
        Test performance with multiple sequential tasks.
        
        Verifies:
        1. Sequential task processing efficiency
        2. Memory management across tasks
        3. Performance degradation monitoring
        4. Resource cleanup between tasks
        """
        try:
            task_count = 5
            total_start_time = time.time()
            execution_times = []
            
            # Set up responses for all tasks
            for i in range(task_count):
                predictable_llm.add_tool_call_response(
                    tool_name="workplan.create_or_update",
                    arguments={
                        "summary": f"Sequential task {i+1} work plan",
                        "items": [{
                            "id": f"sequential_task_{i+1}",
                            "title": f"Sequential Task {i+1}",
                            "description": f"Task number {i+1} in sequence",
                            "kind": "local",
                            "dependencies": []
                        }]
                    },
                    content=f"Created work plan for task {i+1}"
                )
            
            # Execute tasks sequentially
            for i in range(task_count):
                # Clear previous packets to avoid accumulation
                integration_orchestrator._state.inter_packets.clear()
                
                task = integration_task_factory(
                    content=f"Execute sequential performance test task {i+1}",
                    thread_id=f"sequential_thread_{i+1}"
                )
                
                from core.iem.packets import TaskPacket
                from core.iem.models import ElementAddress
                
                task_packet = TaskPacket.create(
                    src=ElementAddress(uid="user"),
                    dst=ElementAddress(uid=integration_orchestrator.uid),
                    task=task
                )
                
                integration_orchestrator._state.inter_packets.append(task_packet)
                
                # Measure individual task performance
                task_start_time = time.time()
                
                with patch.object(integration_orchestrator, 'get_adjacent_nodes', return_value={}), \
                     patch.object(integration_orchestrator, 'send_task', return_value=f"sequential_task_{i+1}"):
                    
                    result = integration_orchestrator.run(integration_orchestrator._state)
                    execution_tracker.track_llm_call()
                    
                    task_end_time = time.time()
                    task_execution_time = task_end_time - task_start_time
                    execution_times.append(task_execution_time)
                    
                    # VERIFY: Each task completes successfully
                    assert result is not None
                    assert task_execution_time < 5.0, f"Task {i+1} took too long: {task_execution_time:.2f}s"
            
            total_end_time = time.time()
            total_execution_time = total_end_time - total_start_time
            avg_execution_time = sum(execution_times) / len(execution_times)
            
            # VERIFY: Overall performance acceptable
            assert total_execution_time < 25.0, f"Sequential tasks took too long: {total_execution_time:.2f}s"
            assert avg_execution_time < 5.0, f"Average task time too high: {avg_execution_time:.2f}s"
            
            # VERIFY: Performance consistency (no significant degradation)
            if len(execution_times) > 1:
                max_time = max(execution_times)
                min_time = min(execution_times)
                time_variance = max_time - min_time
                assert time_variance < 3.0, f"Performance variance too high: {time_variance:.2f}s"
            
            # VERIFY: All tasks processed
            assert predictable_llm.call_count >= task_count
            
            print(f"✅ SEQUENTIAL TASKS PERFORMANCE: {task_count} tasks in {total_execution_time:.2f}s (avg: {avg_execution_time:.3f}s)")
            
        except Exception as e:
            execution_tracker.track_error(str(e))
            pytest.fail(f"Sequential tasks performance test failed: {e}")
    
    def test_concurrent_orchestrator_instances_performance_acceptable(
        self,
        predictable_llm: PredictableLLM,
        orchestrator_integration_state,
        integration_task_factory,
        execution_tracker: ExecutionTracker
    ):
        """
        Test performance with multiple concurrent orchestrator instances.
        
        Verifies:
        1. Concurrent instance execution
        2. Resource contention handling
        3. Performance under concurrency
        4. System stability with multiple instances
        """
        try:
            instance_count = 3
            tasks_per_instance = 2
            
            # Create multiple orchestrator instances
            orchestrators = []
            for i in range(instance_count):
                from elements.nodes.orchestrator.orchestrator_node import OrchestratorNode
                
                orchestrator = OrchestratorNode(llm=predictable_llm)
                
                # Set up context and state for each instance
                from tests.conftest import create_step_context
                step_context = create_step_context(
                    uid=f"concurrent_orchestrator_{i}",
                    adjacent_nodes=["worker_1", "worker_2"]
                )
                orchestrator.set_context(step_context)
                orchestrator._state = orchestrator_integration_state
                
                orchestrators.append(orchestrator)
            
            # Set up LLM responses for all tasks
            total_tasks = instance_count * tasks_per_instance
            for i in range(total_tasks):
                predictable_llm.add_tool_call_response(
                    tool_name="workplan.create_or_update",
                    arguments={
                        "summary": f"Concurrent task {i+1} work plan",
                        "items": [{
                            "id": f"concurrent_task_{i+1}",
                            "title": f"Concurrent Task {i+1}",
                            "description": f"Task {i+1} for concurrency testing",
                            "kind": "local",
                            "dependencies": []
                        }]
                    },
                    content=f"Created concurrent work plan {i+1}"
                )
            
            def execute_orchestrator_tasks(orchestrator_idx):
                """Execute tasks for a single orchestrator instance."""
                orchestrator = orchestrators[orchestrator_idx]
                instance_times = []
                
                for task_idx in range(tasks_per_instance):
                    # Clear packets to avoid cross-contamination
                    orchestrator._state.inter_packets.clear()
                    
                    task = integration_task_factory(
                        content=f"Concurrent task from orchestrator {orchestrator_idx+1}, task {task_idx+1}",
                        thread_id=f"concurrent_thread_{orchestrator_idx}_{task_idx}"
                    )
                    
                    from core.iem.packets import TaskPacket
                    from core.iem.models import ElementAddress
                    
                    task_packet = TaskPacket.create(
                        src=ElementAddress(uid="user"),
                        dst=ElementAddress(uid=orchestrator.uid),
                        task=task
                    )
                    
                    orchestrator._state.inter_packets.append(task_packet)
                    
                    # Execute with timing
                    start_time = time.time()
                    
                    with patch.object(orchestrator, 'get_adjacent_nodes', return_value={}), \
                         patch.object(orchestrator, 'send_task', return_value=f"concurrent_task_{orchestrator_idx}_{task_idx}"):
                        
                        result = orchestrator.run(orchestrator._state)
                        execution_tracker.track_llm_call()
                        
                        end_time = time.time()
                        execution_time = end_time - start_time
                        instance_times.append(execution_time)
                        
                        # Verify individual task success
                        assert result is not None
                
                return instance_times
            
            # Execute concurrently using ThreadPoolExecutor
            start_time = time.time()
            
            with ThreadPoolExecutor(max_workers=instance_count) as executor:
                future_to_instance = {
                    executor.submit(execute_orchestrator_tasks, i): i 
                    for i in range(instance_count)
                }
                
                all_execution_times = []
                for future in as_completed(future_to_instance):
                    instance_idx = future_to_instance[future]
                    try:
                        instance_times = future.result()
                        all_execution_times.extend(instance_times)
                    except Exception as e:
                        pytest.fail(f"Concurrent orchestrator {instance_idx} failed: {e}")
            
            end_time = time.time()
            total_concurrent_time = end_time - start_time
            avg_task_time = sum(all_execution_times) / len(all_execution_times)
            
            # VERIFY: Concurrent performance acceptable
            assert total_concurrent_time < 30.0, f"Concurrent execution took too long: {total_concurrent_time:.2f}s"
            assert avg_task_time < 10.0, f"Average concurrent task time too high: {avg_task_time:.2f}s"
            
            # VERIFY: All tasks completed
            assert len(all_execution_times) == total_tasks
            assert predictable_llm.call_count >= total_tasks
            
            print(f"✅ CONCURRENT INSTANCES PERFORMANCE: {instance_count} instances, {total_tasks} tasks in {total_concurrent_time:.2f}s")
            
        except Exception as e:
            execution_tracker.track_error(str(e))
            pytest.fail(f"Concurrent instances performance test failed: {e}")
    
    def test_large_work_plan_performance_acceptable(
        self,
        integration_orchestrator: OrchestratorNode,
        predictable_llm: PredictableLLM,
        integration_task_factory,
        execution_tracker: ExecutionTracker
    ):
        """
        Test performance with large, complex work plans.
        
        Verifies:
        1. Large work plan processing efficiency
        2. Memory usage with complex plans
        3. Dependency resolution performance
        4. Scalability characteristics
        """
        try:
            # Create task requiring large work plan
            task = integration_task_factory(
                content="Execute large-scale enterprise project with 25+ interconnected work items",
                thread_id="large_plan_thread"
            )
            
            # Generate large work plan with complex dependencies
            work_items = []
            item_count = 25
            
            # Create foundation items (no dependencies)
            for i in range(5):
                work_items.append({
                    "id": f"foundation_{i}",
                    "title": f"Foundation Task {i}",
                    "description": f"Foundation work item {i}",
                    "kind": "local" if i % 2 == 0 else "remote",
                    "dependencies": []
                })
            
            # Create mid-tier items (depend on foundation)
            for i in range(5, 15):
                dependencies = [f"foundation_{j}" for j in range(min(3, i))]
                work_items.append({
                    "id": f"midtier_{i}",
                    "title": f"Mid-tier Task {i}",
                    "description": f"Mid-tier work item {i}",
                    "kind": "local" if i % 3 == 0 else "remote",
                    "dependencies": dependencies
                })
            
            # Create top-tier items (depend on mid-tier)
            for i in range(15, item_count):
                dependencies = [f"midtier_{j}" for j in range(5, min(10, i))]
                work_items.append({
                    "id": f"toptier_{i}",
                    "title": f"Top-tier Task {i}",
                    "description": f"Top-tier work item {i}",
                    "kind": "local" if i % 4 == 0 else "remote",
                    "dependencies": dependencies
                })
            
            # Set up LLM response with large work plan
            predictable_llm.add_tool_call_response(
                tool_name="workplan.create_or_update",
                arguments={
                    "summary": f"Large enterprise project with {item_count} work items",
                    "items": work_items
                },
                content="Created large-scale work plan"
            )
            
            # Create IEM packet
            from core.iem.packets import TaskPacket
            from core.iem.models import ElementAddress
            
            task_packet = TaskPacket.create(
                src=ElementAddress(uid="user"),
                dst=ElementAddress(uid=integration_orchestrator.uid),
                task=task
            )
            
            integration_orchestrator._state.inter_packets.append(task_packet)
            
            # Mock large node network
            from core.enums import ResourceCategory
            
            mock_adjacent_nodes = {
                f"specialized_node_{i}": ElementCard(
                    uid=f"specialized_node_{i}",
                    category=ResourceCategory.NODE,
                    type_key=f"specialized_node_type_{i}",
                    name=f"Specialized Node {i}",
                    description=f"Specialized processing node {i}",
                    capabilities={f"skill_{i}", f"capability_{i}", f"domain_{i % 5}"},
                    reads=set(),
                    writes=set(),
                    instance=None,
                    config={},
                    skills={f"skill_{i}": True, f"capability_{i}": True, f"domain_{i % 5}": True}
                )
                for i in range(15)  # Large node network
            }
            
            # Measure large plan performance
            start_time = time.time()
            start_memory = self._get_memory_usage()
            
            with patch.object(integration_orchestrator, 'get_adjacent_nodes', return_value=mock_adjacent_nodes), \
                 patch.object(integration_orchestrator, 'send_task', return_value="large_plan_task"):
                
                result = integration_orchestrator.run(integration_orchestrator._state)
                execution_tracker.track_llm_call()
                
                end_time = time.time()
                end_memory = self._get_memory_usage()
                
                execution_time = end_time - start_time
                memory_delta = end_memory - start_memory
                
                # VERIFY: Large plan performance acceptable
                assert result is not None
                assert execution_time < 20.0, f"Large plan took too long: {execution_time:.2f}s"
                assert memory_delta < 100 * 1024 * 1024, f"Large plan memory usage too high: {memory_delta / 1024 / 1024:.1f}MB"
                
                # VERIFY: Work plan created successfully
                workspace = integration_orchestrator.get_workspace(task.thread_id)
                plan_service = WorkPlanService(workspace)
                work_plan = plan_service.load(integration_orchestrator.uid)
                
                if work_plan:
                    execution_tracker.track_work_plan_creation(work_plan)
                    assert len(work_plan.items) >= 20, "Should handle large work plan"
                
                print(f"✅ LARGE WORK PLAN PERFORMANCE: {item_count} items in {execution_time:.2f}s, Memory: {memory_delta / 1024 / 1024:.1f}MB")
                
        except Exception as e:
            execution_tracker.track_error(str(e))
            pytest.fail(f"Large work plan performance test failed: {e}")
    
    def _get_memory_usage(self) -> int:
        """Get current memory usage in bytes."""
        try:
            import psutil
            import os
            process = psutil.Process(os.getpid())
            return process.memory_info().rss
        except ImportError:
            # psutil not available, return dummy value
            return 0


@pytest.mark.integration
@pytest.mark.orchestrator
@pytest.mark.performance
class TestOrchestratorResourceManagement:
    """
    Resource management and efficiency tests.
    
    These tests verify that the orchestrator manages system resources
    efficiently and maintains stability under various resource conditions.
    """
    
    def test_memory_management_during_long_execution_acceptable(
        self,
        integration_orchestrator: OrchestratorNode,
        predictable_llm: PredictableLLM,
        integration_task_factory,
        execution_tracker: ExecutionTracker
    ):
        """
        Test memory management during extended execution periods.
        
        Verifies:
        1. Memory usage stability over time
        2. No significant memory leaks
        3. Resource cleanup effectiveness
        4. Long-running performance characteristics
        """
        try:
            task_count = 10
            memory_measurements = []
            
            # Set up responses for extended execution
            for i in range(task_count):
                predictable_llm.add_tool_call_response(
                    tool_name="workplan.create_or_update",
                    arguments={
                        "summary": f"Extended execution task {i+1}",
                        "items": [{
                            "id": f"extended_task_{i+1}",
                            "title": f"Extended Task {i+1}",
                            "description": f"Task for extended execution test {i+1}",
                            "kind": "local",
                            "dependencies": []
                        }]
                    },
                    content=f"Created extended execution plan {i+1}"
                )
            
            # Execute tasks with memory monitoring
            for i in range(task_count):
                # Clear packets between iterations
                integration_orchestrator._state.inter_packets.clear()
                
                # Measure memory before task
                memory_before = self._get_memory_usage()
                
                task = integration_task_factory(
                    content=f"Extended execution test task {i+1}",
                    thread_id=f"extended_thread_{i+1}"
                )
                
                from core.iem.packets import TaskPacket
                from core.iem.models import ElementAddress
                
                task_packet = TaskPacket.create(
                    src=ElementAddress(uid="user"),
                    dst=ElementAddress(uid=integration_orchestrator.uid),
                    task=task
                )
                
                integration_orchestrator._state.inter_packets.append(task_packet)
                
                with patch.object(integration_orchestrator, 'get_adjacent_nodes', return_value={}), \
                     patch.object(integration_orchestrator, 'send_task', return_value=f"extended_task_{i+1}"):
                    
                    result = integration_orchestrator.run(integration_orchestrator._state)
                    execution_tracker.track_llm_call()
                    
                    # Measure memory after task
                    memory_after = self._get_memory_usage()
                    memory_delta = memory_after - memory_before
                    memory_measurements.append(memory_after)
                    
                    # VERIFY: Individual task success and reasonable memory usage
                    assert result is not None
                    assert memory_delta < 20 * 1024 * 1024, f"Task {i+1} memory delta too high: {memory_delta / 1024 / 1024:.1f}MB"
                
                # Small delay to allow cleanup
                time.sleep(0.1)
            
            # VERIFY: Memory stability over time
            if len(memory_measurements) > 1:
                initial_memory = memory_measurements[0]
                final_memory = memory_measurements[-1]
                total_memory_growth = final_memory - initial_memory
                
                # Allow some growth but detect significant leaks
                max_acceptable_growth = 50 * 1024 * 1024  # 50MB
                assert total_memory_growth < max_acceptable_growth, \
                    f"Memory growth too high: {total_memory_growth / 1024 / 1024:.1f}MB"
            
            print(f"✅ MEMORY MANAGEMENT: {task_count} tasks, memory stable")
            
        except Exception as e:
            execution_tracker.track_error(str(e))
            pytest.fail(f"Memory management test failed: {e}")
    
    def _get_memory_usage(self) -> int:
        """Get current memory usage in bytes."""
        try:
            import psutil
            import os
            process = psutil.Process(os.getpid())
            return process.memory_info().rss
        except ImportError:
            # psutil not available, return dummy value
            return 0
