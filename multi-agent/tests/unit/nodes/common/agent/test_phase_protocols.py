"""
Unit tests for phase protocols and models.

Tests the PhaseContextProvider, PhaseToolProvider protocols and
PhaseState, WorkPlanStatus models for correctness and type safety.
"""

import pytest
from unittest.mock import Mock
from typing import List

from elements.nodes.common.agent.phase_protocols import (
    PhaseContextProvider, PhaseToolProvider, PhaseState, WorkPlanStatus,
    create_work_plan_status, create_phase_state, PhaseTransitionPolicy
)
from elements.nodes.common.agent.constants import ExecutionPhase
from elements.tools.common.base_tool import BaseTool


class TestWorkPlanStatus:
    """Test WorkPlanStatus model."""
    
    def test_create_work_plan_status_defaults(self):
        """Test creating WorkPlanStatus with default values."""
        status = create_work_plan_status()
        
        assert status.total_items == 0
        assert status.pending_items == 0
        assert status.in_progress_items == 0
        assert status.waiting_items == 0
        assert status.done_items == 0
        assert status.failed_items == 0
        assert status.blocked_items == 0
        assert status.has_local_ready is False
        assert status.has_remote_waiting is False
        assert status.is_complete is False
    
    def test_create_work_plan_status_with_values(self):
        """Test creating WorkPlanStatus with specific values."""
        status = create_work_plan_status(
            total_items=5,
            pending_items=2,
            in_progress_items=1,
            done_items=2,
            is_complete=True
        )
        
        assert status.total_items == 5
        assert status.pending_items == 2
        assert status.in_progress_items == 1
        assert status.done_items == 2
        assert status.is_complete is True
    
    def test_work_plan_status_immutable(self):
        """Test that WorkPlanStatus is immutable."""
        status = create_work_plan_status(total_items=5)
        
        with pytest.raises(AttributeError):
            status.total_items = 10


class TestPhaseState:
    """Test PhaseState model."""
    
    def test_create_phase_state_defaults(self):
        """Test creating PhaseState with default values."""
        state = create_phase_state()
        
        assert state.work_plan_status is None
        assert state.thread_id is None
        assert state.node_uid is None
        assert state.additional_context is None
    
    def test_create_phase_state_with_values(self):
        """Test creating PhaseState with specific values."""
        work_plan_status = create_work_plan_status(total_items=3)
        state = create_phase_state(
            work_plan_status=work_plan_status,
            thread_id="thread-123",
            node_uid="node-456",
            custom_field="custom_value"
        )
        
        assert state.work_plan_status == work_plan_status
        assert state.thread_id == "thread-123"
        assert state.node_uid == "node-456"
        assert state.additional_context == {"custom_field": "custom_value"}
    
    def test_phase_state_immutable(self):
        """Test that PhaseState is immutable."""
        state = create_phase_state(thread_id="thread-123")
        
        with pytest.raises(AttributeError):
            state.thread_id = "thread-456"


class TestPhaseContextProvider:
    """Test PhaseContextProvider protocol."""
    
    def test_protocol_implementation(self):
        """Test that concrete implementations satisfy the protocol."""
        
        class ConcreteProvider:
            def get_phase_context(self) -> PhaseState:
                return create_phase_state(
                    work_plan_status=create_work_plan_status(total_items=1),
                    thread_id="test-thread"
                )
        
        provider = ConcreteProvider()
        
        # Should satisfy protocol
        assert isinstance(provider, PhaseContextProvider)
        
        # Should return correct type
        context = provider.get_phase_context()
        assert isinstance(context, PhaseState)
        assert context.work_plan_status.total_items == 1
        assert context.thread_id == "test-thread"


class TestPhaseToolProvider:
    """Test PhaseToolProvider protocol."""
    
    def test_protocol_implementation(self):
        """Test that concrete implementations satisfy the protocol."""
        
        mock_tool = Mock(spec=BaseTool)
        mock_tool.name = "test_tool"
        
        class ConcreteProvider:
            def get_tools_for_phase(self, phase: ExecutionPhase) -> List[BaseTool]:
                return [mock_tool] if phase == ExecutionPhase.PLANNING else []
            
            def get_all_phase_tools(self) -> dict:
                return {ExecutionPhase.PLANNING: [mock_tool]}
        
        provider = ConcreteProvider()
        
        # Should satisfy protocol
        assert isinstance(provider, PhaseToolProvider)
        
        # Should return correct tools
        planning_tools = provider.get_tools_for_phase(ExecutionPhase.PLANNING)
        assert len(planning_tools) == 1
        assert planning_tools[0] == mock_tool
        
        allocation_tools = provider.get_tools_for_phase(ExecutionPhase.ALLOCATION)
        assert len(allocation_tools) == 0
        
        all_tools = provider.get_all_phase_tools()
        assert ExecutionPhase.PLANNING in all_tools
        assert all_tools[ExecutionPhase.PLANNING] == [mock_tool]


class TestPhaseTransitionPolicy:
    """Test PhaseTransitionPolicy protocol."""
    
    def test_protocol_implementation(self):
        """Test that concrete implementations satisfy the protocol."""
        
        class ConcretePolicy:
            def decide(self, *, state: PhaseState, current: ExecutionPhase, observations: List) -> ExecutionPhase:
                if state.work_plan_status and state.work_plan_status.total_items == 0:
                    return ExecutionPhase.PLANNING
                return ExecutionPhase.MONITORING
        
        policy = ConcretePolicy()
        
        # Should satisfy protocol
        assert isinstance(policy, PhaseTransitionPolicy)
        
        # Should return correct phase
        empty_state = create_phase_state(
            work_plan_status=create_work_plan_status(total_items=0)
        )
        phase = policy.decide(
            state=empty_state,
            current=ExecutionPhase.ALLOCATION,
            observations=[]
        )
        assert phase == ExecutionPhase.PLANNING
        
        # Test with non-empty plan
        active_state = create_phase_state(
            work_plan_status=create_work_plan_status(total_items=3)
        )
        phase = policy.decide(
            state=active_state,
            current=ExecutionPhase.PLANNING,
            observations=[]
        )
        assert phase == ExecutionPhase.MONITORING


class TestHelperFunctions:
    """Test helper functions."""
    
    def test_create_work_plan_status_type_safety(self):
        """Test that create_work_plan_status enforces types."""
        # Should work with correct types
        status = create_work_plan_status(total_items=5, is_complete=True)
        assert isinstance(status, WorkPlanStatus)
        
        # Test with keyword arguments only (enforced by *)
        with pytest.raises(TypeError):
            create_work_plan_status(5)  # positional argument should fail
    
    def test_create_phase_state_additional_context(self):
        """Test that additional context is properly handled."""
        state = create_phase_state(
            thread_id="test",
            custom_key="custom_value",
            another_key=42
        )
        
        assert state.thread_id == "test"
        assert state.additional_context == {
            "custom_key": "custom_value",
            "another_key": 42
        }
        
        # Test with no additional context
        state_empty = create_phase_state(thread_id="test")
        assert state_empty.additional_context is None


