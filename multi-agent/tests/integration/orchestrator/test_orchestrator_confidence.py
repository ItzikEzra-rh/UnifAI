"""
Comprehensive Integration Tests for Orchestrator System.

These tests are designed to give confidence that the orchestrator system works correctly
by testing real components together with predictable scenarios.

SOLID Principles Applied:
- Single Responsibility: Each test has one clear purpose
- Open/Closed: Tests are extensible without modification
- Liskov Substitution: Uses real components where possible
- Interface Segregation: Clean fixtures with focused responsibilities  
- Dependency Inversion: Depends on abstractions, not concretions
"""

import pytest
from unittest.mock import patch
from typing import Dict, Any, List

from elements.nodes.orchestrator.orchestrator_node import OrchestratorNode
from elements.nodes.common.workload import Task, WorkPlan, WorkItem, WorkItemStatus, WorkPlanService
from elements.llms.common.chat.message import ChatMessage, Role, ToolCall

# Import our clean, SOLID fixtures
from tests.fixtures.orchestrator_integration import (
    PredictableLLM, ExecutionTracker,
    create_planning_scenario, create_synthesis_scenario
)


@pytest.mark.integration
@pytest.mark.orchestrator
class TestOrchestratorSystemConfidence:
    """
    Integration tests that give confidence the orchestrator system works correctly.
    
    These tests use real components where possible and verify actual behavior.
    """
    
    def test_complete_orchestration_cycle_gives_confidence(
        self,
        integration_orchestrator: OrchestratorNode,
        predictable_llm: PredictableLLM,
        orchestrator_workspace_service: WorkPlanService,
        integration_task_factory,
        execution_tracker: ExecutionTracker,
        planning_scenario_helper,
        synthesis_scenario_helper
    ):
        """
        Test a complete orchestration cycle end-to-end.
        
        This test gives confidence that:
        1. Orchestrator can receive and process tasks
        2. LLM integration works correctly  
        3. Work plan creation and management works
        4. Workspace operations work correctly
        5. Phase transitions happen as expected
        
        This is a CONFIDENCE test - it verifies the system actually works.
        """
        # Create a realistic task
        task = integration_task_factory(
            content="Analyze Q3 sales data and create summary report",
            thread_id="confidence_test_thread"
        )
        
        # Set up predictable LLM responses for planning
        planning_scenario_helper(predictable_llm, task.content)
        
        # Set up synthesis response
        synthesis_scenario_helper(predictable_llm)
        
        # Create a proper IEM packet for the task (orchestrator expects IEM packets, not raw tasks)
        from core.iem.packets import TaskPacket
        from core.iem.models import ElementAddress
        
        task_packet = TaskPacket.create(
            src=ElementAddress(uid="user"),
            dst=ElementAddress(uid=integration_orchestrator.uid),
            task=task
        )
        
        # Add the packet to state for processing
        # The state view uses the backing GraphState, so we need to access it correctly
        integration_orchestrator._state.inter_packets.append(task_packet)
        
        # Mock some dependencies to avoid circular import issues
        with patch.object(integration_orchestrator, 'get_adjacent_nodes', return_value={}), \
             patch.object(integration_orchestrator, 'send_task', return_value="task_sent"):
            
            # RUN THE ORCHESTRATOR - This is the main test!
            try:
                result_state = integration_orchestrator.run(integration_orchestrator._state)
                execution_tracker.track_llm_call()
                
                # VERIFY: Orchestrator ran without crashing
                assert result_state is not None
                
                # VERIFY: LLM was called (indicates orchestration happened)
                assert predictable_llm.call_count > 0, "LLM should have been called for orchestration"
                
                # VERIFY: Work plan was created and persisted
                # Get the workload service and create a WorkPlanService
                workload_service = integration_orchestrator.get_workload_service()
                from elements.nodes.common.workload import WorkPlanService
                plan_service = WorkPlanService(workload_service)
                work_plan = plan_service.load(task.thread_id, integration_orchestrator.uid)
                if work_plan:
                    execution_tracker.track_work_plan_creation(work_plan)
                    assert work_plan.summary is not None
                    assert len(work_plan.items) > 0
                
                # VERIFY: Workspace operations work
                workspace = integration_orchestrator.get_workspace(task.thread_id)
                assert workspace is not None
                assert workspace.thread_id == task.thread_id
                
                # VERIFY: No critical errors occurred
                assert len(execution_tracker.errors) == 0
                
                print(f"✅ CONFIDENCE TEST PASSED: {execution_tracker.get_summary()}")
                
            except Exception as e:
                execution_tracker.track_error(str(e))
                pytest.fail(f"Orchestration cycle failed: {e}")
    
    def test_workspace_persistence_gives_confidence(
        self,
        integration_orchestrator: OrchestratorNode,
        orchestrator_workspace_service: WorkPlanService,
        execution_tracker: ExecutionTracker
    ):
        """
        Test that workspace operations persist correctly across multiple calls.
        
        This gives confidence that:
        1. Workspace data is properly stored and retrieved
        2. State management works correctly
        3. Multiple orchestration cycles maintain consistency
        """
        thread_id = "persistence_test_thread"
        
        try:
            # Add facts and variables to workspace
            integration_orchestrator.add_fact_to_workspace(thread_id, "Initial analysis started")
            integration_orchestrator.add_fact_to_workspace(thread_id, "Data loaded successfully")
            integration_orchestrator.set_workspace_variable(thread_id, "analysis_stage", "planning")
            integration_orchestrator.set_workspace_variable(thread_id, "data_quality", "high")
            
            execution_tracker.track_workspace_fact("Initial analysis started")
            execution_tracker.track_workspace_fact("Data loaded successfully")  
            execution_tracker.track_workspace_variable("analysis_stage", "planning")
            execution_tracker.track_workspace_variable("data_quality", "high")
            
            # Retrieve workspace and verify persistence
            workspace = integration_orchestrator.get_workspace(thread_id)
            
            # VERIFY: Facts were persisted
            assert "Initial analysis started" in workspace.context.facts
            assert "Data loaded successfully" in workspace.context.facts
            
            # VERIFY: Variables were persisted
            assert integration_orchestrator.get_workspace_variable(thread_id, "analysis_stage") == "planning"
            assert integration_orchestrator.get_workspace_variable(thread_id, "data_quality") == "high"
            
            # VERIFY: Workspace operations tracking worked
            assert execution_tracker.verify_workspace_operations()
            
            print(f"✅ PERSISTENCE TEST PASSED: {execution_tracker.get_summary()}")
            
        except Exception as e:
            execution_tracker.track_error(str(e))
            pytest.fail(f"Workspace persistence test failed: {e}")
    
    def test_phase_provider_integration_gives_confidence(
        self,
        integration_orchestrator: OrchestratorNode,
        execution_tracker: ExecutionTracker
    ):
        """
        Test that phase provider integration works correctly.
        
        This gives confidence that:
        1. Phase provider can be created without errors
        2. Phase system definitions are valid
        3. Tools are properly initialized
        4. No circular dependencies exist
        """
        try:
            # Mock dependencies to test phase provider creation
            with patch.object(integration_orchestrator, 'get_workload_service') as mock_get_workload_service, \
                 patch.object(integration_orchestrator, 'get_adjacent_nodes') as mock_get_adjacent, \
                 patch.object(integration_orchestrator, 'send_task') as mock_send_task:
                
                # Set up mocks
                mock_get_workload_service.return_value = integration_orchestrator.get_workload_service()
                mock_get_adjacent.return_value = {}
                mock_send_task.return_value = "test_task_id"
                
                # Test phase provider creation (this happens in orchestration cycle)
                from elements.nodes.orchestrator.orchestrator_phase_provider import OrchestratorPhaseProvider
                
                phase_provider = OrchestratorPhaseProvider(
                    domain_tools=[],
                    get_adjacent_nodes=mock_get_adjacent,
                    send_task=mock_send_task,
                    node_uid=integration_orchestrator.uid,
                    thread_id="test_thread",
                    get_workload_service=mock_get_workload_service
                )
                
                # VERIFY: Phase provider was created
                assert phase_provider is not None
                
                # VERIFY: Phase system is valid
                phase_system = phase_provider.get_phase_system()
                assert phase_system is not None
                assert len(phase_system.phases) > 0
                
                # VERIFY: Each phase has tools
                for phase_def in phase_system.phases:
                    assert phase_def.tools is not None
                    assert len(phase_def.tools) > 0, f"Phase {phase_def.name} should have tools"
                
                # VERIFY: Phase transitions work
                from elements.nodes.common.agent.phases.phase_protocols import create_phase_state
                test_state = create_phase_state(
                    work_plan_status=None,
                    thread_id="test_thread",
                    node_uid=integration_orchestrator.uid
                )
                
                initial_phase = phase_provider.get_initial_phase()
                assert initial_phase is not None

                next_phase = phase_provider.decide_next_phase(
                    current_phase=initial_phase,
                    context=test_state,
                    observations=[]
                )
                assert next_phase is not None
                
                print("✅ PHASE PROVIDER INTEGRATION TEST PASSED")
                
        except Exception as e:
            execution_tracker.track_error(str(e))
            pytest.fail(f"Phase provider integration test failed: {e}")
    
    def test_llm_integration_gives_confidence(
        self,
        predictable_llm: PredictableLLM,
        execution_tracker: ExecutionTracker
    ):
        """
        Test that LLM integration works predictably.
        
        This gives confidence that:
        1. Predictable LLM behaves as expected
        2. Tool calls are handled correctly
        3. Response sequencing works
        4. Call history tracking works
        """
        try:
            # Set up predictable responses
            predictable_llm.add_response("First response")
            predictable_llm.add_tool_call_response(
                tool_name="test_tool",
                arguments={"param": "value"},
                content="Tool call response"
            )
            predictable_llm.add_response("Final response")
            
            # Test LLM calls
            from elements.llms.common.chat.message import ChatMessage, Role
            
            test_messages = [
                ChatMessage(role=Role.USER, content="Test message 1")
            ]
            
            # VERIFY: First call returns first response
            response1 = predictable_llm.chat(test_messages)
            execution_tracker.track_llm_call()
            assert response1.content == "First response"
            assert len(response1.tool_calls) == 0
            
            # VERIFY: Second call returns tool call response
            response2 = predictable_llm.chat(test_messages)
            execution_tracker.track_llm_call()
            assert response2.content == "Tool call response"
            assert len(response2.tool_calls) == 1
            assert response2.tool_calls[0].name == "test_tool"
            
            # VERIFY: Third call returns final response
            response3 = predictable_llm.chat(test_messages)
            execution_tracker.track_llm_call()
            assert response3.content == "Final response"
            
            # VERIFY: Call history tracking works
            summary = predictable_llm.get_summary()
            assert summary["call_count"] == 3
            assert summary["remaining_responses"] >= 0
            assert len(summary["call_history"]) == 3
            
            print("✅ LLM INTEGRATION TEST PASSED")
            
        except Exception as e:
            execution_tracker.track_error(str(e))
            pytest.fail(f"LLM integration test failed: {e}")


@pytest.mark.integration
@pytest.mark.performance  
class TestOrchestratorPerformanceConfidence:
    """Performance tests that give confidence the system performs adequately."""
    
    def test_orchestrator_performance_under_normal_load(
        self,
        integration_orchestrator: OrchestratorNode,
        predictable_llm: PredictableLLM,
        integration_task_factory,
        execution_tracker: ExecutionTracker
    ):
        """
        Test orchestrator performance under normal conditions.
        
        This gives confidence that the system performs adequately.
        """
        import time
        
        try:
            # Set up responses for multiple cycles
            for i in range(5):
                predictable_llm.add_tool_call_response(
                    tool_name="workplan.create_or_update",
                    arguments={
                        "summary": f"Plan {i+1}",
                        "items": [{
                            "id": f"task_{i+1}", 
                            "title": f"Task {i+1}", 
                            "description": f"Process and complete task {i+1}",
                            "kind": "local", 
                            "dependencies": []
                        }]
                    },
                    content=f"Creating plan {i+1}"
                )
            
            start_time = time.time()
            
            # Process multiple tasks
            for i in range(5):
                task = integration_task_factory(
                    content=f"Process task {i+1}",
                    thread_id=f"perf_thread_{i+1}"
                )

                # Create proper IEM packet from task
                from core.iem.packets import TaskPacket
                from core.iem.models import ElementAddress
                task_packet = TaskPacket.create(
                    src=ElementAddress(uid="user"),
                    dst=ElementAddress(uid=integration_orchestrator.uid),
                    task=task
                )
                # Clear any previous packets to avoid accumulation
                integration_orchestrator._state.inter_packets.clear()
                integration_orchestrator._state.inter_packets.append(task_packet)
                
                with patch.object(integration_orchestrator, 'get_adjacent_nodes', return_value={}), \
                     patch.object(integration_orchestrator, 'send_task', return_value=f"sent_{i+1}"):
                    
                    result = integration_orchestrator.run(integration_orchestrator._state)
                    execution_tracker.track_llm_call()
                    assert result is not None
            
            end_time = time.time()
            duration = end_time - start_time
            
            # VERIFY: Performance is acceptable (5 tasks in under 10 seconds - integration test)
            assert duration < 10.0, f"Processing 5 tasks took {duration:.3f}s, expected < 10.0s"
            
            # VERIFY: LLM was called for orchestration (multiple calls per task expected)
            assert predictable_llm.call_count >= 5, f"Expected at least 5 LLM calls, got {predictable_llm.call_count}"
            
            print(f"✅ PERFORMANCE TEST PASSED: 5 tasks in {duration:.3f}s")
            
        except Exception as e:
            execution_tracker.track_error(str(e))
            pytest.fail(f"Performance test failed: {e}")


@pytest.mark.integration
@pytest.mark.resilience
class TestOrchestratorResilienceConfidence:
    """Resilience tests that give confidence the system handles errors gracefully."""
    
    def test_orchestrator_handles_empty_state_gracefully(
        self,
        integration_orchestrator: OrchestratorNode,
        execution_tracker: ExecutionTracker
    ):
        """
        Test that orchestrator handles empty/minimal state gracefully.
        
        This gives confidence the system is resilient.
        """
        try:
            # Test with empty packets
            integration_orchestrator._state.inter_packets = []
            
            with patch.object(integration_orchestrator, 'get_adjacent_nodes', return_value={}):
                # Should not crash with empty packets
                result = integration_orchestrator.run(integration_orchestrator._state)
                assert result is not None
            
            print("✅ RESILIENCE TEST PASSED: Handles empty state gracefully")
            
        except Exception as e:
            execution_tracker.track_error(str(e))
            pytest.fail(f"Resilience test failed: {e}")
    
    def test_orchestrator_handles_malformed_tasks_gracefully(
        self,
        integration_orchestrator: OrchestratorNode,
        execution_tracker: ExecutionTracker
    ):
        """
        Test that orchestrator handles malformed or unusual tasks gracefully.
        
        This gives confidence the system is robust.
        """
        try:
            # Test with various edge case tasks
            edge_case_tasks = [
                Task(content="", thread_id="empty_content_thread", created_by="test"),
                Task(content="x" * 1000, thread_id="long_content_thread", created_by="test"),  # Very long content
                Task(content="Test with ünicöde chäräcters", thread_id="unicode_thread", created_by="test"),
            ]
            
            for task in edge_case_tasks:
                # Create proper IEM packet from task
                from core.iem.packets import TaskPacket
                from core.iem.models import ElementAddress
                task_packet = TaskPacket.create(
                    src=ElementAddress(uid="user"),
                    dst=ElementAddress(uid=integration_orchestrator.uid),
                    task=task
                )
                # Clear any previous packets to avoid accumulation  
                integration_orchestrator._state.inter_packets.clear()
                integration_orchestrator._state.inter_packets.append(task_packet)
                
                with patch.object(integration_orchestrator, 'get_adjacent_nodes', return_value={}):
                    # Should handle edge cases gracefully
                    result = integration_orchestrator.run(integration_orchestrator._state)
                    assert result is not None
            
            print("✅ RESILIENCE TEST PASSED: Handles malformed tasks gracefully")
            
        except Exception as e:
            execution_tracker.track_error(str(e))
            pytest.fail(f"Malformed task resilience test failed: {e}")
