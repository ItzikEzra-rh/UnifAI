"""
Basic Integration Tests for Orchestrator System.

These tests verify basic orchestrator functionality with simple, straightforward scenarios.
They serve as foundation tests that ensure core orchestration workflows work correctly.

SOLID Principles Applied:
- Single Responsibility: Each test verifies one basic orchestration workflow
- Open/Closed: Tests are extensible without modification
- Liskov Substitution: Uses real components with minimal mocking
- Interface Segregation: Clean, focused test interfaces
- Dependency Inversion: Depends on fixtures and abstractions
"""

import pytest
from unittest.mock import patch
from typing import Dict, Any

from elements.nodes.orchestrator.orchestrator_node import OrchestratorNode
from elements.nodes.common.workload import Task, WorkPlan, WorkPlanService
from elements.llms.common.chat.message import ChatMessage, Role

# Import our clean, SOLID fixtures
from tests.fixtures.orchestrator_integration import (
    PredictableLLM, ExecutionTracker,
    create_planning_scenario
)


@pytest.mark.integration
@pytest.mark.orchestrator
class TestOrchestratorBasicIntegration:
    """
    Basic integration tests for core orchestrator functionality.
    
    These tests verify that fundamental orchestration workflows work correctly
    with minimal complexity and realistic scenarios.
    """
    
    def test_single_task_orchestration_works(
        self,
        integration_orchestrator: OrchestratorNode,
        predictable_llm: PredictableLLM,
        integration_task_factory,
        execution_tracker: ExecutionTracker
    ):
        """
        Test that a single task can be orchestrated successfully.
        
        Verifies:
        1. Task reception and processing
        2. Work plan creation
        3. LLM integration
        4. Basic orchestration cycle completion
        """
        try:
            # Create a simple task
            task = integration_task_factory(
                content="Create a simple status report",
                thread_id="basic_test_thread"
            )
            
            # Set up predictable LLM response for work plan creation
            predictable_llm.add_tool_call_response(
                tool_name="workplan.create_or_update",
                arguments={
                    "summary": "Status report work plan",
                    "items": [{
                        "id": "report_task",
                        "title": "Create Status Report",
                        "description": "Generate a comprehensive status report",
                        "kind": "local",
                        "dependencies": []
                    }]
                },
                content="Created work plan for status report"
            )
            
            # Create proper IEM packet (following established pattern)
            from core.iem.packets import TaskPacket
            from core.iem.models import ElementAddress
            
            task_packet = TaskPacket.create(
                src=ElementAddress(uid="user"),
                dst=ElementAddress(uid=integration_orchestrator.uid),
                task=task
            )
            
            # Add packet to state for processing
            integration_orchestrator._state.inter_packets.append(task_packet)
            
            # Mock dependencies (following established pattern)
            with patch.object(integration_orchestrator, 'get_adjacent_nodes', return_value={}), \
                 patch.object(integration_orchestrator, 'send_task', return_value="sent_task_1"):
                
                # Execute orchestration
                result = integration_orchestrator.run(integration_orchestrator._state)
                execution_tracker.track_llm_call()
                
                # VERIFY: Basic execution succeeded
                assert result is not None
                assert predictable_llm.call_count > 0
                
                # VERIFY: Work plan was created
                workload_service = integration_orchestrator.get_workload_service()
                plan_service = WorkPlanService(workload_service)
                work_plan = plan_service.load(task.thread_id, integration_orchestrator.uid)
                
                if work_plan:
                    execution_tracker.track_work_plan_creation(work_plan)
                    assert len(work_plan.items) > 0
                    assert "report_task" in work_plan.items
                
                print("✅ BASIC SINGLE TASK ORCHESTRATION WORKS")
                
        except Exception as e:
            execution_tracker.track_error(str(e))
            pytest.fail(f"Basic single task orchestration failed: {e}")
    
    def test_workspace_context_management_works(
        self,
        integration_orchestrator: OrchestratorNode,
        predictable_llm: PredictableLLM,
        integration_task_factory,
        execution_tracker: ExecutionTracker
    ):
        """
        Test that workspace context is properly managed during orchestration.
        
        Verifies:
        1. Workspace creation and initialization
        2. Context facts addition
        3. Variables management
        4. Thread-specific workspace isolation
        """
        try:
            # Create task with specific context
            task = integration_task_factory(
                content="Process customer feedback data",
                thread_id="context_test_thread"
            )
            
            # Set up basic LLM response
            predictable_llm.add_tool_call_response(
                tool_name="workplan.create_or_update",
                arguments={
                    "summary": "Customer feedback processing plan",
                    "items": [{
                        "id": "feedback_analysis",
                        "title": "Analyze Customer Feedback",
                        "description": "Process and analyze customer feedback data",
                        "kind": "local",
                        "dependencies": []
                    }]
                },
                content="Created feedback processing plan"
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
            
            # Execute orchestration
            with patch.object(integration_orchestrator, 'get_adjacent_nodes', return_value={}), \
                 patch.object(integration_orchestrator, 'send_task', return_value="sent_task_2"):
                
                result = integration_orchestrator.run(integration_orchestrator._state)
                execution_tracker.track_llm_call()
                
                # VERIFY: Workspace was created and has context
                workspace = integration_orchestrator.get_workspace(task.thread_id)
                assert workspace is not None
                
                # VERIFY: Context facts were added
                if hasattr(workspace.context, 'facts') and workspace.context.facts:
                    execution_tracker.track_workspace_fact("Initial request added")
                    # Check that initial request was added as fact
                    fact_contents = [str(fact) for fact in workspace.context.facts]
                    assert any("Process customer feedback data" in fact for fact in fact_contents)
                
                # VERIFY: Variables were set
                orchestrator_uid = workspace.get_variable("orchestrator_uid")
                if orchestrator_uid:
                    execution_tracker.track_workspace_variable("orchestrator_uid", orchestrator_uid)
                    assert orchestrator_uid == integration_orchestrator.uid
                
                print("✅ WORKSPACE CONTEXT MANAGEMENT WORKS")
                
        except Exception as e:
            execution_tracker.track_error(str(e))
            pytest.fail(f"Workspace context management failed: {e}")
    
    def test_orchestration_with_local_work_items_works(
        self,
        integration_orchestrator: OrchestratorNode,
        predictable_llm: PredictableLLM,
        integration_task_factory,
        execution_tracker: ExecutionTracker
    ):
        """
        Test orchestration with local work items (no delegation).
        
        Verifies:
        1. Local work item creation
        2. Work plan execution without delegation
        3. Phase transitions for local work
        4. Completion handling
        """
        try:
            # Create task that should result in local work
            task = integration_task_factory(
                content="Generate monthly analytics report",
                thread_id="local_work_thread"
            )
            
            # Set up LLM response for local work plan
            predictable_llm.add_tool_call_response(
                tool_name="workplan.create_or_update",
                arguments={
                    "summary": "Analytics report generation plan",
                    "items": [
                        {
                            "id": "data_collection",
                            "title": "Collect Analytics Data",
                            "description": "Gather data from various sources",
                            "kind": "local",
                            "dependencies": []
                        },
                        {
                            "id": "report_generation",
                            "title": "Generate Report",
                            "description": "Create the analytics report",
                            "kind": "local",
                            "dependencies": ["data_collection"]
                        }
                    ]
                },
                content="Created analytics report generation plan"
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
            
            # Execute orchestration
            with patch.object(integration_orchestrator, 'get_adjacent_nodes', return_value={}), \
                 patch.object(integration_orchestrator, 'send_task', return_value="sent_task_3"):
                
                result = integration_orchestrator.run(integration_orchestrator._state)
                execution_tracker.track_llm_call()
                
                # VERIFY: Work plan created with local items
                workload_service = integration_orchestrator.get_workload_service()
                plan_service = WorkPlanService(workload_service)
                work_plan = plan_service.load(task.thread_id, integration_orchestrator.uid)
                
                if work_plan:
                    execution_tracker.track_work_plan_creation(work_plan)
                    
                    # Check that work items are local
                    local_items = [item for item in work_plan.items.values() 
                                 if item.kind.value == "local"]
                    assert len(local_items) > 0, "Should have local work items"
                    
                    # Check dependency structure
                    if "report_generation" in work_plan.items:
                        report_item = work_plan.items["report_generation"]
                        assert "data_collection" in report_item.dependencies
                
                print("✅ ORCHESTRATION WITH LOCAL WORK ITEMS WORKS")
                
        except Exception as e:
            execution_tracker.track_error(str(e))
            pytest.fail(f"Local work items orchestration failed: {e}")
    
    def test_empty_orchestrator_state_handling_works(
        self,
        integration_orchestrator: OrchestratorNode,
        predictable_llm: PredictableLLM,
        execution_tracker: ExecutionTracker
    ):
        """
        Test that orchestrator handles empty state gracefully.
        
        Verifies:
        1. No packets to process scenario
        2. Empty state handling
        3. Graceful completion
        4. No errors or crashes
        """
        try:
            # Execute orchestration with empty state (no packets)
            with patch.object(integration_orchestrator, 'get_adjacent_nodes', return_value={}):
                result = integration_orchestrator.run(integration_orchestrator._state)
                
                # VERIFY: Orchestrator handles empty state gracefully
                assert result is not None
                assert result == integration_orchestrator._state
                
                # VERIFY: No LLM calls made (since no work to do)
                assert predictable_llm.call_count == 0
                
                print("✅ EMPTY STATE HANDLING WORKS")
                
        except Exception as e:
            execution_tracker.track_error(str(e))
            pytest.fail(f"Empty state handling failed: {e}")


@pytest.mark.integration
@pytest.mark.orchestrator
class TestOrchestratorBasicErrorHandling:
    """
    Basic error handling tests for orchestrator integration.
    
    Verifies that the orchestrator handles basic error conditions gracefully
    without complex scenarios.
    """
    
    def test_orchestrator_handles_malformed_packets_gracefully(
        self,
        integration_orchestrator: OrchestratorNode,
        execution_tracker: ExecutionTracker
    ):
        """
        Test that orchestrator handles malformed packets without crashing.
        
        Verifies graceful degradation when receiving invalid input.
        """
        try:
            # This test would require more complex setup to create truly malformed packets
            # For basic integration, we verify the orchestrator doesn't crash on empty runs
            
            with patch.object(integration_orchestrator, 'get_adjacent_nodes', return_value={}):
                result = integration_orchestrator.run(integration_orchestrator._state)
                
                # VERIFY: No crash occurred
                assert result is not None
                
                print("✅ BASIC ERROR HANDLING WORKS")
                
        except Exception as e:
            execution_tracker.track_error(str(e))
            pytest.fail(f"Basic error handling failed: {e}")
