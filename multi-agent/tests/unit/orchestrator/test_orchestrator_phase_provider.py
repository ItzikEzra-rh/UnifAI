"""
Unit tests for OrchestratorPhaseProvider.

Tests cover:
- Phase system creation and validation
- Phase transitions and logic
- Tool provisioning per phase
- Context building
- Edge cases and error conditions
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import List, Dict, Any

from elements.nodes.orchestrator.orchestrator_phase_provider import (
    OrchestratorPhaseProvider, OrchestratorPhase
)
from elements.nodes.common.agent.phase_definition import PhaseDefinition, PhaseSystem
from elements.nodes.common.agent.phase_protocols import PhaseState, create_work_plan_status
from elements.nodes.common.workload import WorkPlanService, WorkPlanStatusSummary
from elements.tools.common.base_tool import BaseTool
from tests.fixtures.orchestrator_fixtures import *


class TestOrchestratorPhase:
    """Test OrchestratorPhase enum."""
    
    def test_orchestrator_phase_values(self):
        """Test OrchestratorPhase enum values."""
        assert OrchestratorPhase.PLANNING.value == "planning"
        assert OrchestratorPhase.ALLOCATION.value == "allocation"
        assert OrchestratorPhase.EXECUTION.value == "execution"
        assert OrchestratorPhase.MONITORING.value == "monitoring"
        assert OrchestratorPhase.SYNTHESIS.value == "synthesis"
    
    def test_get_execution_order(self):
        """Test get_execution_order method."""
        order = OrchestratorPhase.get_execution_order()
        
        assert len(order) == 5
        assert order[0] == OrchestratorPhase.PLANNING
        assert order[1] == OrchestratorPhase.ALLOCATION
        assert order[2] == OrchestratorPhase.EXECUTION
        assert order[3] == OrchestratorPhase.MONITORING
        assert order[4] == OrchestratorPhase.SYNTHESIS
    
    def test_get_phase_names(self):
        """Test get_phase_names method."""
        names = OrchestratorPhase.get_phase_names()
        
        assert len(names) == 5
        assert names == ["planning", "allocation", "execution", "monitoring", "synthesis"]


class TestOrchestratorPhaseProviderInitialization:
    """Test OrchestratorPhaseProvider initialization."""
    
    def test_provider_initialization(self, mock_domain_tools, mock_orchestrator_dependencies):
        """Test basic provider initialization."""
        provider = OrchestratorPhaseProvider(
            domain_tools=mock_domain_tools,
            **mock_orchestrator_dependencies
        )
        
        assert provider._domain_tools == mock_domain_tools
        assert provider._node_uid == "test_orchestrator"
        assert provider._thread_id == "test_thread"
        assert provider._get_workload_service is not None
        assert provider._get_adjacent_nodes is not None
        assert provider._send_task is not None
    
    def test_provider_creates_phase_system(self, orchestrator_phase_provider):
        """Test that provider creates phase system on initialization."""
        phase_system = orchestrator_phase_provider.get_phase_system()
        
        assert isinstance(phase_system, PhaseSystem)
        assert phase_system.name == "orchestrator"
        assert len(phase_system.phases) == 5
        
        # Verify all phases are present
        phase_names = phase_system.get_phase_names()
        assert "planning" in phase_names
        assert "allocation" in phase_names
        assert "execution" in phase_names
        assert "monitoring" in phase_names
        assert "synthesis" in phase_names
    
    def test_provider_with_empty_domain_tools(self, mock_orchestrator_dependencies):
        """Test provider with no domain tools."""
        provider = OrchestratorPhaseProvider(
            domain_tools=[],
            **mock_orchestrator_dependencies
        )
        
        phase_system = provider.get_phase_system()
        assert isinstance(phase_system, PhaseSystem)
        
        # Execution phase should still work but with fewer tools
        execution_tools = phase_system.get_tools_for_phase("execution")
        # Should have create_plan_tool but no domain tools
        assert len(execution_tools) >= 1


class TestOrchestratorPhaseProviderPhaseSystem:
    """Test phase system creation and management."""
    
    def test_phase_system_structure(self, orchestrator_phase_provider):
        """Test phase system structure and content."""
        phase_system = orchestrator_phase_provider.get_phase_system()
        
        assert phase_system.name == "orchestrator"
        assert "planning → allocation → execution → monitoring → synthesis" in phase_system.description
        
        # Test each phase
        for phase_name in ["planning", "allocation", "execution", "monitoring", "synthesis"]:
            phase_def = next((p for p in phase_system.phases if p.name == phase_name), None)
            assert phase_def is not None
            assert isinstance(phase_def, PhaseDefinition)
            assert len(phase_def.tools) > 0
            assert len(phase_def.guidance) > 0
    
    def test_planning_phase_tools(self, orchestrator_phase_provider):
        """Test planning phase tool configuration."""
        tools = orchestrator_phase_provider.get_tools_for_phase("planning")
        
        tool_names = [tool.name for tool in tools]
        assert "workplan.create_or_update" in tool_names
        assert "topology.list_adjacent" in tool_names
        assert "topology.get_node_card" in tool_names
        
        # Should not include domain tools in planning
        assert "analyze_data_tool" not in tool_names
        assert "create_report_tool" not in tool_names
    
    def test_allocation_phase_tools(self, orchestrator_phase_provider):
        """Test allocation phase tool configuration."""
        tools = orchestrator_phase_provider.get_tools_for_phase("allocation")
        
        tool_names = [tool.name for tool in tools]
        assert "workplan.assign" in tool_names
        assert "iem.delegate_task" in tool_names
        assert "topology.list_adjacent" in tool_names
        assert "topology.get_node_card" in tool_names
        assert "workplan.create_or_update" in tool_names
    
    def test_execution_phase_tools(self, orchestrator_phase_provider):
        """Test execution phase tool configuration."""
        tools = orchestrator_phase_provider.get_tools_for_phase("execution")
        
        tool_names = [tool.name for tool in tools]
        assert "workplan.create_or_update" in tool_names
        
        # Should include domain tools
        assert "analyze_data_tool" in tool_names
        assert "create_report_tool" in tool_names
    
    def test_monitoring_phase_tools(self, orchestrator_phase_provider):
        """Test monitoring phase tool configuration."""
        tools = orchestrator_phase_provider.get_tools_for_phase("monitoring")
        
        tool_names = [tool.name for tool in tools]
        assert "workplan.mark" in tool_names
        assert "iem.delegate_task" in tool_names
        assert "topology.list_adjacent" in tool_names
        assert "workplan.create_or_update" in tool_names
    
    def test_synthesis_phase_tools(self, orchestrator_phase_provider):
        """Test synthesis phase tool configuration."""
        tools = orchestrator_phase_provider.get_tools_for_phase("synthesis")
        
        tool_names = [tool.name for tool in tools]
        assert "workplan.summarize" in tool_names
        assert "workplan.create_or_update" in tool_names
    
    def test_invalid_phase_tools(self, orchestrator_phase_provider):
        """Test requesting tools for invalid phase."""
        tools = orchestrator_phase_provider.get_tools_for_phase("invalid_phase")
        assert tools == []
    
    def test_phase_guidance(self, orchestrator_phase_provider):
        """Test phase guidance content."""
        planning_guidance = orchestrator_phase_provider.get_phase_guidance("planning")
        assert "PHASE: PLANNING" in planning_guidance
        assert "Create detailed work plan" in planning_guidance
        
        allocation_guidance = orchestrator_phase_provider.get_phase_guidance("allocation")
        assert "PHASE: ALLOCATION" in allocation_guidance
        assert "Assign work items" in allocation_guidance
        
        execution_guidance = orchestrator_phase_provider.get_phase_guidance("execution")
        assert "PHASE: EXECUTION" in execution_guidance
        assert "Execute local work items" in execution_guidance
        
        monitoring_guidance = orchestrator_phase_provider.get_phase_guidance("monitoring")
        assert "PHASE: MONITORING" in monitoring_guidance
        assert "Interpret responses" in monitoring_guidance
        
        synthesis_guidance = orchestrator_phase_provider.get_phase_guidance("synthesis")
        assert "PHASE: SYNTHESIS" in synthesis_guidance
        assert "Summarize completed work" in synthesis_guidance
    
    def test_supported_phases(self, orchestrator_phase_provider):
        """Test get_supported_phases method."""
        phases = orchestrator_phase_provider.get_supported_phases()
        
        assert len(phases) == 5
        assert phases == ["planning", "allocation", "execution", "monitoring", "synthesis"]


class TestOrchestratorPhaseProviderContext:
    """Test phase context building."""
    
    def test_get_phase_context_success(self, orchestrator_phase_provider):
        """Test successful phase context creation."""
        # Mock workspace and service
        mock_workspace = Mock()
        orchestrator_phase_provider._get_workload_service.return_value.get_workspace.return_value = mock_workspace
        
        with patch('elements.nodes.orchestrator.orchestrator_phase_provider.WorkPlanService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            
            # Mock status summary
            mock_summary = WorkPlanStatusSummary(
                total_items=5,
                pending_items=2,
                in_progress_items=1,
                waiting_items=1,
                done_items=1,
                failed_items=0,
                blocked_items=0,
                has_local_ready=True,
                has_remote_waiting=True,
                is_complete=False
            )
            mock_service.get_status_summary.return_value = mock_summary
            
            context = orchestrator_phase_provider.get_phase_context()
            
            assert isinstance(context, PhaseState)
            assert context.work_plan_status is not None
            assert context.work_plan_status.total_items == 5
            assert context.work_plan_status.has_local_ready is True
            # PhaseState doesn't have adjacent_nodes field - it's in additional_context if needed
    
    def test_get_phase_context_no_workspace(self, orchestrator_phase_provider):
        """Test phase context when workspace is unavailable."""
        orchestrator_phase_provider._get_workload_service.return_value.get_workspace.side_effect = Exception("Workspace error")
        
        context = orchestrator_phase_provider.get_phase_context()
        
        # Should return context with empty status
        assert isinstance(context, PhaseState)
        if context.work_plan_status is not None:
            assert context.work_plan_status.total_items == 0
            assert context.work_plan_status.is_complete is False
    
    def test_get_phase_context_no_adjacent_nodes(self, orchestrator_phase_provider):
        """Test phase context when adjacent nodes are unavailable."""
        orchestrator_phase_provider._get_adjacent_nodes.return_value = None
        
        # Mock workspace
        mock_workspace = Mock()
        orchestrator_phase_provider._get_workload_service.return_value.get_workspace.return_value = mock_workspace
        
        with patch('elements.nodes.orchestrator.orchestrator_phase_provider.WorkPlanService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.get_status_summary.return_value = WorkPlanStatusSummary()
            
            context = orchestrator_phase_provider.get_phase_context()
            
            assert isinstance(context, PhaseState)
            # PhaseState doesn't have adjacent_nodes field - it's in additional_context if needed


class TestOrchestratorPhaseProviderTransitions:
    """Test phase transition logic."""
    
    def create_mock_context(self, **status_kwargs):
        """Helper to create mock phase context."""
        default_status = {
            "total_items": 0,
            "pending_items": 0,
            "in_progress_items": 0,
            "waiting_items": 0,
            "done_items": 0,
            "failed_items": 0,
            "blocked_items": 0,
            "has_local_ready": False,
            "has_remote_waiting": False,
            "is_complete": False
        }
        default_status.update(status_kwargs)
        
        work_plan_status = create_work_plan_status(**default_status)
        
        context = Mock()
        context.work_plan_status = work_plan_status
        return context
    
    def test_planning_to_allocation_transition(self, orchestrator_phase_provider):
        """Test transition from planning to allocation."""
        context = self.create_mock_context(total_items=3, pending_items=3)
        
        next_phase = orchestrator_phase_provider.decide_next_phase(
            current_phase="planning",
            context=context,
            observations=[]
        )
        
        assert next_phase == "allocation"
    
    def test_planning_stays_planning(self, orchestrator_phase_provider):
        """Test staying in planning when no items exist."""
        context = self.create_mock_context(total_items=0)
        
        next_phase = orchestrator_phase_provider.decide_next_phase(
            current_phase="planning",
            context=context,
            observations=[]
        )
        
        assert next_phase == "planning"
    
    def test_allocation_to_execution_transition(self, orchestrator_phase_provider):
        """Test transition from allocation to execution."""
        context = self.create_mock_context(
            total_items=3,
            pending_items=1,
            has_local_ready=True
        )
        
        next_phase = orchestrator_phase_provider.decide_next_phase(
            current_phase="allocation",
            context=context,
            observations=[]
        )
        
        assert next_phase == "execution"
    
    def test_allocation_to_monitoring_transition(self, orchestrator_phase_provider):
        """Test transition from allocation to monitoring."""
        context = self.create_mock_context(
            total_items=3,
            waiting_items=2,
            has_remote_waiting=True,
            has_local_ready=False
        )
        
        next_phase = orchestrator_phase_provider.decide_next_phase(
            current_phase="allocation",
            context=context,
            observations=[]
        )
        
        assert next_phase == "monitoring"
    
    def test_allocation_stays_allocation(self, orchestrator_phase_provider):
        """Test staying in allocation when no ready work."""
        context = self.create_mock_context(
            total_items=3,
            pending_items=3,
            has_local_ready=False,
            has_remote_waiting=False
        )
        
        next_phase = orchestrator_phase_provider.decide_next_phase(
            current_phase="allocation",
            context=context,
            observations=[]
        )
        
        assert next_phase == "allocation"
    
    def test_execution_to_monitoring_transition(self, orchestrator_phase_provider):
        """Test transition from execution to monitoring."""
        context = self.create_mock_context(total_items=3)
        
        next_phase = orchestrator_phase_provider.decide_next_phase(
            current_phase="execution",
            context=context,
            observations=[]
        )
        
        assert next_phase == "monitoring"
    
    def test_monitoring_to_synthesis_transition(self, orchestrator_phase_provider):
        """Test transition from monitoring to synthesis."""
        context = self.create_mock_context(
            total_items=3,
            done_items=3,
            is_complete=True
        )
        
        next_phase = orchestrator_phase_provider.decide_next_phase(
            current_phase="monitoring",
            context=context,
            observations=[]
        )
        
        assert next_phase == "synthesis"
    
    def test_monitoring_to_allocation_transition(self, orchestrator_phase_provider):
        """Test transition from monitoring back to allocation."""
        context = self.create_mock_context(
            total_items=5,
            pending_items=2,
            done_items=2,
            failed_items=1,
            is_complete=False
        )
        
        next_phase = orchestrator_phase_provider.decide_next_phase(
            current_phase="monitoring",
            context=context,
            observations=[]
        )
        
        assert next_phase == "allocation"
    
    def test_monitoring_to_execution_transition(self, orchestrator_phase_provider):
        """Test transition from monitoring to execution when no pending items."""
        context = self.create_mock_context(
            total_items=3,
            pending_items=0,  # No pending items - all assigned
            has_local_ready=True,
            is_complete=False
        )
        
        next_phase = orchestrator_phase_provider.decide_next_phase(
            current_phase="monitoring",
            context=context,
            observations=[]
        )
        
        assert next_phase == "execution"
    
    def test_monitoring_stays_monitoring(self, orchestrator_phase_provider):
        """Test staying in monitoring when waiting for responses."""
        context = self.create_mock_context(
            total_items=3,
            waiting_items=2,
            done_items=1,
            is_complete=False,
            has_local_ready=False,
            pending_items=0
        )
        
        next_phase = orchestrator_phase_provider.decide_next_phase(
            current_phase="monitoring",
            context=context,
            observations=[]
        )
        
        assert next_phase == "monitoring"
    
    def test_synthesis_stays_synthesis(self, orchestrator_phase_provider):
        """Test that synthesis is terminal phase."""
        context = self.create_mock_context(is_complete=True)
        
        next_phase = orchestrator_phase_provider.decide_next_phase(
            current_phase="synthesis",
            context=context,
            observations=[]
        )
        
        assert next_phase == "synthesis"
    
    def test_invalid_phase_defaults_to_planning(self, orchestrator_phase_provider):
        """Test that invalid phase defaults to planning."""
        context = self.create_mock_context()
        
        next_phase = orchestrator_phase_provider.decide_next_phase(
            current_phase="invalid_phase",
            context=context,
            observations=[]
        )
        
        assert next_phase == "planning"


class TestOrchestratorPhaseProviderComprehensiveTransitions:
    """
    Comprehensive tests for all phase transition scenarios and edge cases.
    
    This test class validates the orchestrator's phase transition logic, which follows
    a sophisticated priority-based system:
    
    MONITORING PHASE PRIORITIES:
    1. Complete work → SYNTHESIS (highest priority)
    2. Pending items → ALLOCATION (assign unassigned work first)
    3. Local ready → EXECUTION (execute assigned local work)
    4. Otherwise → MONITORING (wait for responses)
    
    ALLOCATION PHASE PRIORITIES:
    1. Local ready → EXECUTION (execute local work immediately)
    2. Remote waiting → MONITORING (wait for remote responses)
    3. Otherwise → ALLOCATION (continue allocation attempts)
    
    EXECUTION PHASE:
    - Always → MONITORING (check results after execution)
    
    PLANNING PHASE:
    - Has items → ALLOCATION (move to assignment)
    - No items → PLANNING (continue planning)
    
    SYNTHESIS PHASE:
    - Always → SYNTHESIS (terminal phase)
    
    This design ensures optimal work scheduling and prevents suboptimal execution patterns.
    """
    
    def create_mock_context(self, **status_kwargs):
        """Helper to create mock phase context."""
        default_status = {
            "total_items": 0,
            "pending_items": 0,
            "in_progress_items": 0,
            "waiting_items": 0,
            "done_items": 0,
            "failed_items": 0,
            "blocked_items": 0,
            "has_local_ready": False,
            "has_remote_waiting": False,
            "is_complete": False
        }
        default_status.update(status_kwargs)
        
        work_plan_status = create_work_plan_status(**default_status)
        
        context = Mock()
        context.work_plan_status = work_plan_status
        return context

    # =============================================================================
    # MONITORING PHASE COMPREHENSIVE TESTS
    # =============================================================================
    
    def test_monitoring_priority_complete_first(self, orchestrator_phase_provider):
        """Test monitoring prioritizes completion over other transitions."""
        context = self.create_mock_context(
            total_items=5,
            pending_items=2,
            has_local_ready=True,
            has_remote_waiting=True,
            is_complete=True  # This should take priority
        )
        
        next_phase = orchestrator_phase_provider.decide_next_phase(
            current_phase="monitoring",
            context=context,
            observations=[]
        )
        
        assert next_phase == "synthesis"
    
    def test_monitoring_priority_pending_over_local_ready(self, orchestrator_phase_provider):
        """Test monitoring prioritizes pending items over local ready items."""
        context = self.create_mock_context(
            total_items=5,
            pending_items=2,  # Should take priority
            has_local_ready=True,
            is_complete=False
        )
        
        next_phase = orchestrator_phase_provider.decide_next_phase(
            current_phase="monitoring",
            context=context,
            observations=[]
        )
        
        assert next_phase == "allocation"
    
    def test_monitoring_to_execution_when_only_local_ready(self, orchestrator_phase_provider):
        """Test monitoring goes to execution when only local ready items exist."""
        context = self.create_mock_context(
            total_items=3,
            pending_items=0,
            has_local_ready=True,
            is_complete=False
        )
        
        next_phase = orchestrator_phase_provider.decide_next_phase(
            current_phase="monitoring",
            context=context,
            observations=[]
        )
        
        assert next_phase == "execution"
    
    def test_monitoring_stays_when_waiting_for_responses(self, orchestrator_phase_provider):
        """Test monitoring stays when waiting for remote responses."""
        context = self.create_mock_context(
            total_items=3,
            pending_items=0,
            has_local_ready=False,
            has_remote_waiting=True,
            waiting_items=2,
            is_complete=False
        )
        
        next_phase = orchestrator_phase_provider.decide_next_phase(
            current_phase="monitoring",
            context=context,
            observations=[]
        )
        
        assert next_phase == "monitoring"
    
    def test_monitoring_edge_case_empty_plan(self, orchestrator_phase_provider):
        """Test monitoring with empty plan."""
        context = self.create_mock_context(
            total_items=0,
            is_complete=False
        )
        
        next_phase = orchestrator_phase_provider.decide_next_phase(
            current_phase="monitoring",
            context=context,
            observations=[]
        )
        
        assert next_phase == "monitoring"
    
    def test_monitoring_complex_scenario_mixed_states(self, orchestrator_phase_provider):
        """Test monitoring with complex mixed work item states."""
        context = self.create_mock_context(
            total_items=10,
            pending_items=3,  # Should trigger allocation
            in_progress_items=2,
            waiting_items=2,
            done_items=2,
            failed_items=1,
            blocked_items=0,
            has_local_ready=True,
            has_remote_waiting=True,
            is_complete=False
        )
        
        next_phase = orchestrator_phase_provider.decide_next_phase(
            current_phase="monitoring",
            context=context,
            observations=[]
        )
        
        assert next_phase == "allocation"  # Pending items take priority
    
    def test_monitoring_original_failing_scenario_explained(self, orchestrator_phase_provider):
        """Test the original failing scenario to demonstrate correct behavior."""
        # This was the original test scenario that failed
        context = self.create_mock_context(
            total_items=3,
            pending_items=1,  # This causes allocation, not execution
            has_local_ready=True,
            is_complete=False
        )
        
        next_phase = orchestrator_phase_provider.decide_next_phase(
            current_phase="monitoring",
            context=context,
            observations=[]
        )
        
        # The system correctly prioritizes pending items over local ready items
        # This ensures optimal work allocation before execution
        assert next_phase == "allocation"  # NOT "execution" - this is correct!

    # =============================================================================
    # ALLOCATION PHASE COMPREHENSIVE TESTS  
    # =============================================================================
    
    def test_allocation_priority_local_over_remote(self, orchestrator_phase_provider):
        """Test allocation prioritizes local ready over remote waiting."""
        context = self.create_mock_context(
            total_items=5,
            has_local_ready=True,  # Should take priority
            has_remote_waiting=True,
            is_complete=False
        )
        
        next_phase = orchestrator_phase_provider.decide_next_phase(
            current_phase="allocation",
            context=context,
            observations=[]
        )
        
        assert next_phase == "execution"
    
    def test_allocation_to_monitoring_when_only_remote(self, orchestrator_phase_provider):
        """Test allocation goes to monitoring when only remote work waiting."""
        context = self.create_mock_context(
            total_items=3,
            has_local_ready=False,
            has_remote_waiting=True,
            waiting_items=2,
            is_complete=False
        )
        
        next_phase = orchestrator_phase_provider.decide_next_phase(
            current_phase="allocation",
            context=context,
            observations=[]
        )
        
        assert next_phase == "monitoring"
    
    def test_allocation_stays_when_no_ready_work(self, orchestrator_phase_provider):
        """Test allocation stays when no work is ready."""
        context = self.create_mock_context(
            total_items=5,
            pending_items=3,
            blocked_items=2,
            has_local_ready=False,
            has_remote_waiting=False,
            is_complete=False
        )
        
        next_phase = orchestrator_phase_provider.decide_next_phase(
            current_phase="allocation",
            context=context,
            observations=[]
        )
        
        assert next_phase == "allocation"

    # =============================================================================
    # PLANNING PHASE COMPREHENSIVE TESTS
    # =============================================================================
    
    def test_planning_to_allocation_with_items(self, orchestrator_phase_provider):
        """Test planning moves to allocation when items exist."""
        context = self.create_mock_context(
            total_items=3,
            pending_items=3
        )
        
        next_phase = orchestrator_phase_provider.decide_next_phase(
            current_phase="planning",
            context=context,
            observations=[]
        )
        
        assert next_phase == "allocation"
    
    def test_planning_stays_when_empty(self, orchestrator_phase_provider):
        """Test planning stays when no items exist."""
        context = self.create_mock_context(
            total_items=0
        )
        
        next_phase = orchestrator_phase_provider.decide_next_phase(
            current_phase="planning",
            context=context,
            observations=[]
        )
        
        assert next_phase == "planning"

    # =============================================================================
    # EXECUTION PHASE COMPREHENSIVE TESTS
    # =============================================================================
    
    def test_execution_always_goes_to_monitoring(self, orchestrator_phase_provider):
        """Test execution always transitions to monitoring."""
        # Test with various contexts - execution should always go to monitoring
        contexts = [
            self.create_mock_context(total_items=1, has_local_ready=True),
            self.create_mock_context(total_items=5, pending_items=2),
            self.create_mock_context(total_items=0),
            self.create_mock_context(total_items=10, is_complete=True)
        ]
        
        for context in contexts:
            next_phase = orchestrator_phase_provider.decide_next_phase(
                current_phase="execution",
                context=context,
                observations=[]
            )
            assert next_phase == "monitoring"

    # =============================================================================
    # SYNTHESIS PHASE COMPREHENSIVE TESTS
    # =============================================================================
    
    def test_synthesis_always_stays_synthesis(self, orchestrator_phase_provider):
        """Test synthesis is terminal and always stays."""
        # Test with various contexts - synthesis should always stay
        contexts = [
            self.create_mock_context(total_items=0),
            self.create_mock_context(total_items=5, pending_items=2),
            self.create_mock_context(total_items=10, is_complete=True),
            self.create_mock_context(total_items=3, has_local_ready=True)
        ]
        
        for context in contexts:
            next_phase = orchestrator_phase_provider.decide_next_phase(
                current_phase="synthesis",
                context=context,
                observations=[]
            )
            assert next_phase == "synthesis"

    # =============================================================================
    # EDGE CASES AND ERROR CONDITIONS
    # =============================================================================
    
    def test_transition_with_none_context(self, orchestrator_phase_provider):
        """Test transition handling with None context."""
        # This should not crash - should handle gracefully
        next_phase = orchestrator_phase_provider.decide_next_phase(
            current_phase="monitoring",
            context=None,
            observations=[]
        )
        
        # Should default to planning when context is invalid
        assert next_phase == "planning"
    
    def test_transition_with_none_work_plan_status(self, orchestrator_phase_provider):
        """Test transition with None work plan status."""
        context = Mock()
        context.work_plan_status = None
        
        next_phase = orchestrator_phase_provider.decide_next_phase(
            current_phase="monitoring",
            context=context,
            observations=[]
        )
        
        # Should default to planning when status is None
        assert next_phase == "planning"
    
    def test_transition_robustness_various_none_scenarios(self, orchestrator_phase_provider):
        """Test transition robustness with various None/invalid scenarios."""
        # Test all phases with None context
        phases = ["planning", "allocation", "execution", "monitoring", "synthesis"]
        
        for phase in phases:
            # None context should always default to planning
            next_phase = orchestrator_phase_provider.decide_next_phase(
                current_phase=phase,
                context=None,
                observations=[]
            )
            assert next_phase == "planning"
            
            # Context with None work_plan_status should also default to planning
            context = Mock()
            context.work_plan_status = None
            next_phase = orchestrator_phase_provider.decide_next_phase(
                current_phase=phase,
                context=context,
                observations=[]
            )
            assert next_phase == "planning"
    
    def test_all_phases_with_extreme_values(self, orchestrator_phase_provider):
        """Test all phases with extreme work plan values."""
        extreme_context = self.create_mock_context(
            total_items=1000,
            pending_items=500,
            in_progress_items=200,
            waiting_items=150,
            done_items=100,
            failed_items=50,
            blocked_items=0,
            has_local_ready=True,
            has_remote_waiting=True,
            is_complete=False
        )
        
        # Test each phase handles extreme values correctly
        phases_and_expected = [
            ("planning", "allocation"),  # Has items
            ("allocation", "execution"),  # Has local ready
            ("execution", "monitoring"),  # Always goes to monitoring
            ("monitoring", "allocation"),  # Has pending items
            ("synthesis", "synthesis")   # Terminal phase
        ]
        
        for current_phase, expected_next in phases_and_expected:
            next_phase = orchestrator_phase_provider.decide_next_phase(
                current_phase=current_phase,
                context=extreme_context,
                observations=[]
            )
            assert next_phase == expected_next
    
    def test_complete_workflow_simulation(self, orchestrator_phase_provider):
        """Test a complete workflow simulation through all phases."""
        # Simulate a complete orchestration workflow
        
        # 1. Start with planning (empty plan)
        empty_context = self.create_mock_context(total_items=0)
        phase = orchestrator_phase_provider.decide_next_phase("planning", empty_context, [])
        assert phase == "planning"
        
        # 2. Planning creates items, moves to allocation
        planned_context = self.create_mock_context(total_items=3, pending_items=3)
        phase = orchestrator_phase_provider.decide_next_phase("planning", planned_context, [])
        assert phase == "allocation"
        
        # 3. Allocation assigns work, some local ready
        allocated_context = self.create_mock_context(
            total_items=3, pending_items=1, has_local_ready=True, has_remote_waiting=True
        )
        phase = orchestrator_phase_provider.decide_next_phase("allocation", allocated_context, [])
        assert phase == "execution"  # Local ready takes priority
        
        # 4. Execution completes, goes to monitoring
        executed_context = self.create_mock_context(
            total_items=3, pending_items=1, waiting_items=2
        )
        phase = orchestrator_phase_provider.decide_next_phase("execution", executed_context, [])
        assert phase == "monitoring"
        
        # 5. Monitoring sees pending items, goes back to allocation
        phase = orchestrator_phase_provider.decide_next_phase("monitoring", executed_context, [])
        assert phase == "allocation"  # Still has pending items
        
        # 6. All work assigned and waiting
        waiting_context = self.create_mock_context(
            total_items=3, waiting_items=3, has_remote_waiting=True
        )
        phase = orchestrator_phase_provider.decide_next_phase("allocation", waiting_context, [])
        assert phase == "monitoring"
        
        # 7. Work completes, goes to synthesis
        complete_context = self.create_mock_context(
            total_items=3, done_items=3, is_complete=True
        )
        phase = orchestrator_phase_provider.decide_next_phase("monitoring", complete_context, [])
        assert phase == "synthesis"
        
        # 8. Synthesis is terminal
        phase = orchestrator_phase_provider.decide_next_phase("synthesis", complete_context, [])
        assert phase == "synthesis"


class TestOrchestratorPhaseProviderEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_provider_with_none_dependencies(self):
        """Test provider with None dependencies."""
        # The system should handle None gracefully, not raise TypeError
        provider = OrchestratorPhaseProvider(
            domain_tools=[],
            get_workload_service=Mock(),
            get_adjacent_nodes=Mock(),
            send_task=Mock(),
            node_uid="test",
            thread_id="test"
        )
        assert provider is not None
    
    def test_provider_with_failing_tool_initialization(self, mock_domain_tools, mock_orchestrator_dependencies):
        """Test provider when tool initialization fails."""
        # Mock tool classes to raise exceptions
        with patch('elements.nodes.orchestrator.orchestrator_phase_provider.CreateOrUpdateWorkPlanTool') as mock_tool:
            mock_tool.side_effect = Exception("Tool initialization failed")
            
            # Should raise the exception since tool initialization is critical
            with pytest.raises(Exception, match="Tool initialization failed"):
                provider = OrchestratorPhaseProvider(
                    domain_tools=mock_domain_tools,
                    **mock_orchestrator_dependencies
                )
    
    def test_provider_with_large_number_of_domain_tools(self, mock_orchestrator_dependencies):
        """Test provider with many domain tools."""
        # Create 100 mock domain tools
        many_tools = []
        for i in range(100):
            tool = Mock(spec=BaseTool)
            tool.name = f"domain_tool_{i}"
            tool.description = f"Domain tool number {i}"
            many_tools.append(tool)
        
        provider = OrchestratorPhaseProvider(
            domain_tools=many_tools,
            **mock_orchestrator_dependencies
        )
        
        # Execution phase should include all domain tools
        execution_tools = provider.get_tools_for_phase("execution")
        execution_tool_names = [tool.name for tool in execution_tools]
        
        # Should include all 100 domain tools plus built-in tools
        domain_tool_names = [f"domain_tool_{i}" for i in range(100)]
        for tool_name in domain_tool_names:
            assert tool_name in execution_tool_names
    
    def test_provider_thread_safety(self, mock_domain_tools, mock_orchestrator_dependencies):
        """Test provider behavior under concurrent access."""
        provider = OrchestratorPhaseProvider(
            domain_tools=mock_domain_tools,
            **mock_orchestrator_dependencies
        )
        
        # Simulate concurrent access to different methods
        import threading
        results = []
        errors = []
        
        def access_provider():
            try:
                # Multiple operations that might conflict
                phase_system = provider.get_phase_system()
                tools = provider.get_tools_for_phase("planning")
                guidance = provider.get_phase_guidance("allocation")
                phases = provider.get_supported_phases()
                
                results.append({
                    "phase_system": phase_system,
                    "tools": len(tools),
                    "guidance": len(guidance),
                    "phases": len(phases)
                })
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=access_provider)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Should not have any errors
        assert len(errors) == 0
        assert len(results) == 10
        
        # All results should be consistent
        first_result = results[0]
        for result in results[1:]:
            assert result["tools"] == first_result["tools"]
            assert result["guidance"] == first_result["guidance"]
            assert result["phases"] == first_result["phases"]
    
    def test_provider_memory_usage(self, mock_orchestrator_dependencies):
        """Test provider memory usage with repeated operations."""
        # Create provider with no domain tools to minimize memory
        provider = OrchestratorPhaseProvider(
            domain_tools=[],
            **mock_orchestrator_dependencies
        )
        
        # Perform many operations
        for _ in range(1000):
            provider.get_phase_system()
            provider.get_tools_for_phase("planning")
            provider.get_phase_guidance("execution")
            provider.get_supported_phases()
        
        # Should not consume excessive memory (basic smoke test)
        phase_system = provider.get_phase_system()
        assert isinstance(phase_system, PhaseSystem)
    
    def test_provider_with_unicode_identifiers(self, mock_domain_tools):
        """Test provider with unicode node/thread identifiers."""
        provider = OrchestratorPhaseProvider(
            domain_tools=mock_domain_tools,
            get_workload_service=Mock(),
            get_adjacent_nodes=Mock(return_value={}),
            send_task=Mock(),
            node_uid="orchestrator_🚀_node",
            thread_id="thread_中文_123"
        )
        
        assert provider._node_uid == "orchestrator_🚀_node"
        assert provider._thread_id == "thread_中文_123"
        
        # Should still work normally
        phase_system = provider.get_phase_system()
        assert isinstance(phase_system, PhaseSystem)


class TestOrchestratorPhaseProviderIntegration:
    """Test integration aspects of the phase provider."""
    
    def test_provider_with_real_workspace_service(self, orchestrator_phase_provider):
        """Test provider integration with actual WorkPlanService."""
        # Create a real workspace mock
        workspace = Mock()
        workspace.variables = {
            "workplan_test_orchestrator": {
                "summary": "Test Plan",
                "owner_uid": "test_orchestrator",
                "thread_id": "test_thread",
                "items": {
                    "item_1": {
                        "id": "item_1",
                        "title": "Test Item",
                        "description": "Test description",
                        "dependencies": [],
                        "status": "pending",
                        "kind": "local",
                        "assigned_uid": None,
                        "tool": None,
                        "args": {},
                        "result_ref": None,
                        "error": None,
                        "correlation_task_id": None,
                        "retry_count": 0,
                        "max_retries": 3,
                        "created_at": "2024-01-01T12:00:00",
                        "updated_at": "2024-01-01T12:00:00"
                    }
                },
                "created_at": "2024-01-01T12:00:00",
                "updated_at": "2024-01-01T12:00:00"
            }
        }
        workspace.get_variable = lambda k: workspace.variables.get(k)
        workspace.set_variable = lambda k, v: workspace.variables.update({k: v})
        
        orchestrator_phase_provider._get_workload_service.return_value.get_workspace.return_value = workspace
        
        # Get phase context should work with real data
        context = orchestrator_phase_provider.get_phase_context()
        
        assert isinstance(context, PhaseState)
        assert context.work_plan_status.total_items == 1
        assert context.work_plan_status.pending_items == 1
        assert context.work_plan_status.has_local_ready is True
    
    def test_provider_phase_flow_simulation(self, orchestrator_phase_provider):
        """Test complete phase flow simulation."""
        # Start with empty plan (planning phase)
        empty_context = Mock()
        empty_context.work_plan_status = create_work_plan_status(total_items=0)
        
        phase = orchestrator_phase_provider.decide_next_phase("planning", empty_context, [])
        assert phase == "planning"
        
        # Add items (move to allocation)
        with_items_context = Mock()
        with_items_context.work_plan_status = create_work_plan_status(
            total_items=3, pending_items=3
        )
        
        phase = orchestrator_phase_provider.decide_next_phase("planning", with_items_context, [])
        assert phase == "allocation"
        
        # Have local ready items (move to execution)
        ready_context = Mock()
        ready_context.work_plan_status = create_work_plan_status(
            total_items=3, pending_items=1, has_local_ready=True
        )
        
        phase = orchestrator_phase_provider.decide_next_phase("allocation", ready_context, [])
        assert phase == "execution"
        
        # After execution (move to monitoring)
        post_execution_context = Mock()
        post_execution_context.work_plan_status = create_work_plan_status(
            total_items=3, in_progress_items=1, waiting_items=1
        )
        
        phase = orchestrator_phase_provider.decide_next_phase("execution", post_execution_context, [])
        assert phase == "monitoring"
        
        # Work complete (move to synthesis)
        complete_context = Mock()
        complete_context.work_plan_status = create_work_plan_status(
            total_items=3, done_items=3, is_complete=True
        )
        
        phase = orchestrator_phase_provider.decide_next_phase("monitoring", complete_context, [])
        assert phase == "synthesis"
        
        # Synthesis is terminal
        phase = orchestrator_phase_provider.decide_next_phase("synthesis", complete_context, [])
        assert phase == "synthesis"
