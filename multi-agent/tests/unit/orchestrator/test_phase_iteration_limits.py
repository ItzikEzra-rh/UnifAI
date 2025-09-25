"""
Unit tests for phase iteration limits system.

Tests the Pydantic models and phase provider iteration tracking to ensure
infinite loops are prevented and limits are enforced correctly.
"""

import pytest
from unittest.mock import Mock

from elements.nodes.orchestrator.phases.models import (
    PhaseIterationLimits, PhaseIterationState
)
from elements.nodes.orchestrator.orchestrator_phase_provider import (
    OrchestratorPhaseProvider, OrchestratorPhase
)
from elements.nodes.common.agent.phases.phase_protocols import create_phase_state, create_work_plan_status


class TestPhaseIterationLimits:
    """Test PhaseIterationLimits Pydantic model."""
    
    def test_default_limits(self):
        """Test that default limits are 10 for all phases."""
        limits = PhaseIterationLimits()
        
        assert limits.planning == 10
        assert limits.allocation == 10
        assert limits.execution == 10
        assert limits.monitoring == 10
        assert limits.synthesis == 10
    
    def test_custom_limits(self):
        """Test custom limits configuration."""
        limits = PhaseIterationLimits(
            planning=5,
            allocation=8,
            execution=3,
            monitoring=15,
            synthesis=2
        )
        
        assert limits.planning == 5
        assert limits.allocation == 8
        assert limits.execution == 3
        assert limits.monitoring == 15
        assert limits.synthesis == 2
    
    def test_validation_positive_limits(self):
        """Test that limits must be positive."""
        with pytest.raises(ValueError):
            PhaseIterationLimits(planning=0)
        
        with pytest.raises(ValueError):
            PhaseIterationLimits(allocation=-1)
    
    def test_get_limit(self):
        """Test get_limit method."""
        limits = PhaseIterationLimits(planning=7, allocation=12)
        
        assert limits.get_limit("planning") == 7
        assert limits.get_limit("allocation") == 12
        assert limits.get_limit("unknown_phase") == 10  # Default
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        limits = PhaseIterationLimits(planning=3, monitoring=20)
        result = limits.to_dict()
        
        expected = {
            "planning": 3,
            "allocation": 10,  # Default
            "execution": 10,   # Default
            "monitoring": 20,
            "synthesis": 10    # Default
        }
        assert result == expected


class TestPhaseIterationState:
    """Test PhaseIterationState Pydantic model."""
    
    def test_default_state(self):
        """Test that default state is all zeros."""
        state = PhaseIterationState()
        
        assert state.planning == 0
        assert state.allocation == 0
        assert state.execution == 0
        assert state.monitoring == 0
        assert state.synthesis == 0
    
    def test_get_count(self):
        """Test get_count method."""
        state = PhaseIterationState(planning=3, allocation=7)
        
        assert state.get_count("planning") == 3
        assert state.get_count("allocation") == 7
        assert state.get_count("execution") == 0
        assert state.get_count("unknown_phase") == 0  # Default
    
    def test_increment_immutable(self):
        """Test that increment returns new instance (immutable)."""
        state1 = PhaseIterationState(planning=2)
        state2 = state1.increment("planning")
        
        # Original state unchanged
        assert state1.planning == 2
        
        # New state incremented
        assert state2.planning == 3
        assert state2.allocation == 0  # Other fields preserved
        
        # Different objects
        assert state1 is not state2
    
    def test_increment_unknown_phase(self):
        """Test increment with unknown phase name."""
        state1 = PhaseIterationState()
        state2 = state1.increment("unknown_phase")
        
        # Should return same state for unknown phases
        assert state1.model_dump() == state2.model_dump()
    
    def test_reset_immutable(self):
        """Test that reset returns new instance (immutable)."""
        state1 = PhaseIterationState(planning=5, allocation=3)
        state2 = state1.reset("planning")
        
        # Original state unchanged
        assert state1.planning == 5
        assert state1.allocation == 3
        
        # New state with planning reset
        assert state2.planning == 0
        assert state2.allocation == 3  # Other fields preserved
        
        # Different objects
        assert state1 is not state2
    
    def test_is_exceeded(self):
        """Test is_exceeded method."""
        state = PhaseIterationState(planning=5, allocation=10, execution=3)
        limits = PhaseIterationLimits(planning=5, allocation=10, execution=10)
        
        # Exactly at limit (should be exceeded)
        assert state.is_exceeded("planning", limits) is True
        assert state.is_exceeded("allocation", limits) is True
        
        # Below limit
        assert state.is_exceeded("execution", limits) is False
        
        # Unknown phase (should not be exceeded)
        assert state.is_exceeded("unknown_phase", limits) is False


class TestOrchestratorPhaseProviderIterations:
    """Test iteration tracking in OrchestratorPhaseProvider."""
    
    @pytest.fixture
    def mock_dependencies(self):
        """Create mocked dependencies for phase provider."""
        return {
            'domain_tools': [],
            'get_adjacent_nodes': Mock(return_value={}),
            'send_task': Mock(),
            'node_uid': 'test_node',
            'thread_id': 'test_thread',
            'get_workload_service': Mock()
        }
    
    @pytest.fixture
    def phase_provider(self, mock_dependencies):
        """Create phase provider with default limits."""
        return OrchestratorPhaseProvider(**mock_dependencies)
    
    @pytest.fixture  
    def custom_phase_provider(self, mock_dependencies):
        """Create phase provider with custom limits."""
        custom_limits = PhaseIterationLimits(
            planning=2, allocation=3, execution=1, monitoring=5, synthesis=1
        )
        return OrchestratorPhaseProvider(
            iteration_limits=custom_limits,
            **mock_dependencies
        )
    
    def test_initial_iteration_state(self, phase_provider):
        """Test that initial iteration counts are zero."""
        assert phase_provider._iteration_state.planning == 0
        assert phase_provider._iteration_state.allocation == 0
        assert phase_provider._iteration_state.execution == 0
        assert phase_provider._iteration_state.monitoring == 0
        assert phase_provider._iteration_state.synthesis == 0
    
    def test_increment_phase_iteration(self, phase_provider):
        """Test incrementing phase iterations."""
        # Initial state
        assert phase_provider._iteration_state.get_count("planning") == 0
        
        # Increment once
        phase_provider.increment_phase_iteration("planning")
        assert phase_provider._iteration_state.get_count("planning") == 1
        
        # Increment again
        phase_provider.increment_phase_iteration("planning")
        assert phase_provider._iteration_state.get_count("planning") == 2
        
        # Other phases unaffected
        assert phase_provider._iteration_state.get_count("allocation") == 0
    
    def test_reset_phase_iteration(self, phase_provider):
        """Test resetting phase iterations."""
        # Set up some iterations
        phase_provider.increment_phase_iteration("planning")
        phase_provider.increment_phase_iteration("planning")
        phase_provider.increment_phase_iteration("allocation")
        
        assert phase_provider._iteration_state.get_count("planning") == 2
        assert phase_provider._iteration_state.get_count("allocation") == 1
        
        # Reset planning
        phase_provider.reset_phase_iteration("planning")
        assert phase_provider._iteration_state.get_count("planning") == 0
        assert phase_provider._iteration_state.get_count("allocation") == 1  # Unaffected
    
    def test_is_phase_limit_exceeded_default(self, phase_provider):
        """Test limit checking with default limits (10)."""
        # Under limit
        for _ in range(9):
            phase_provider.increment_phase_iteration("planning")
        assert phase_provider.is_phase_limit_exceeded("planning") is False
        
        # At limit (should be exceeded)
        phase_provider.increment_phase_iteration("planning")
        assert phase_provider.is_phase_limit_exceeded("planning") is True
    
    def test_is_phase_limit_exceeded_custom(self, custom_phase_provider):
        """Test limit checking with custom limits."""
        # Planning limit is 2
        custom_phase_provider.increment_phase_iteration("planning")
        assert custom_phase_provider.is_phase_limit_exceeded("planning") is False
        
        custom_phase_provider.increment_phase_iteration("planning")
        assert custom_phase_provider.is_phase_limit_exceeded("planning") is True
        
        # Allocation limit is 3
        for _ in range(3):
            custom_phase_provider.increment_phase_iteration("allocation")
        assert custom_phase_provider.is_phase_limit_exceeded("allocation") is True
    
    def test_decide_next_phase_respects_limits(self, custom_phase_provider):
        """Test that decide_next_phase respects iteration limits."""
        # Mock context with work items
        status = create_work_plan_status(
            total_items=2,
            pending_items=2,
            has_local_ready=True,
            is_complete=False
        )
        context = create_phase_state(work_plan_status=status)
        
        # Planning phase should normally transition to allocation
        result = custom_phase_provider.decide_next_phase("planning", context, [])
        assert result == "allocation"  # Normal transition
        
        # Exceed planning limit (2 iterations)
        custom_phase_provider.increment_phase_iteration("planning")
        custom_phase_provider.increment_phase_iteration("planning")
        
        # Should now handle limit exceeded (go to allocation anyway if we have items)
        result = custom_phase_provider.decide_next_phase("planning", context, [])
        assert result == "allocation"  # Limit exceeded, but we have items
        
        # Planning count should be reset when transitioning
        assert custom_phase_provider._iteration_state.get_count("planning") == 0
    
    def test_decide_next_phase_limit_exceeded_no_progress(self, custom_phase_provider):
        """Test limit exceeded when no progress can be made."""
        # Mock context with no work items  
        status = create_work_plan_status(
            total_items=0,
            pending_items=0,
            has_local_ready=False,
            is_complete=False
        )
        context = create_phase_state(work_plan_status=status)
        
        # Exceed planning limit with no items to work with
        custom_phase_provider.increment_phase_iteration("planning")
        custom_phase_provider.increment_phase_iteration("planning")
        
        # Should force terminal synthesis when stuck in planning with no progress
        result = custom_phase_provider.decide_next_phase("planning", context, [])
        assert result == "synthesis"  # Terminal state
    
    def test_handle_phase_limit_exceeded_allocation(self, custom_phase_provider):
        """Test limit exceeded handling for allocation phase."""
        # Mock context with local work ready
        status = create_work_plan_status(
            total_items=2,
            pending_items=1,
            has_local_ready=True,
            is_complete=False
        )
        context = create_phase_state(work_plan_status=status)
        
        # Exceed allocation limit (3 iterations)
        for _ in range(3):
            custom_phase_provider.increment_phase_iteration("allocation")
        
        # Should transition to execution when allocation stuck but local work available
        result = custom_phase_provider.decide_next_phase("allocation", context, [])
        assert result == "execution"
    
    def test_handle_phase_limit_exceeded_monitoring(self, custom_phase_provider):
        """Test limit exceeded handling for monitoring phase."""
        # Mock context with incomplete work
        status = create_work_plan_status(
            total_items=2,
            pending_items=1,
            has_local_ready=False,
            is_complete=False
        )
        context = create_phase_state(work_plan_status=status)
        
        # Exceed monitoring limit (5 iterations)
        for _ in range(5):
            custom_phase_provider.increment_phase_iteration("monitoring")
        
        # Should force synthesis when monitoring stuck (waiting too long)
        result = custom_phase_provider.decide_next_phase("monitoring", context, [])
        assert result == "synthesis"


class TestPhaseIterationIntegration:
    """Integration tests for the complete iteration limit system."""
    
    def test_phase_definition_includes_limits(self):
        """Test that PhaseDefinition includes max_iterations from limits."""
        custom_limits = PhaseIterationLimits(planning=7, allocation=12)
        
        mock_dependencies = {
            'domain_tools': [],
            'get_adjacent_nodes': Mock(return_value={}),
            'send_task': Mock(),
            'node_uid': 'test_node',
            'thread_id': 'test_thread',
            'get_workload_service': Mock()
        }
        
        provider = OrchestratorPhaseProvider(
            iteration_limits=custom_limits,
            **mock_dependencies
        )
        
        # Check that phase definitions have correct limits
        planning_phase = provider._phase_system.get_phase("planning")
        allocation_phase = provider._phase_system.get_phase("allocation")
        
        assert planning_phase.max_iterations == 7
        assert allocation_phase.max_iterations == 12
    
    def test_realistic_orchestration_scenario(self):
        """Test a realistic orchestration scenario with limits."""
        # Setup with low limits for testing
        custom_limits = PhaseIterationLimits(
            planning=2, allocation=3, execution=2, monitoring=4, synthesis=1
        )
        
        mock_dependencies = {
            'domain_tools': [],
            'get_adjacent_nodes': Mock(return_value={"node_1": {}, "node_2": {}}),
            'send_task': Mock(),
            'node_uid': 'orchestrator',
            'thread_id': 'workflow_123',
            'get_workload_service': Mock()
        }
        
        provider = OrchestratorPhaseProvider(
            iteration_limits=custom_limits,
            **mock_dependencies
        )
        
        # Simulate orchestration flow
        current_phase = "planning"
        
        # Planning phase - eventually creates work items
        status = create_work_plan_status(total_items=0, is_complete=False)
        context = create_phase_state(work_plan_status=status)
        
        # First planning iteration - no items yet
        provider.increment_phase_iteration(current_phase)
        current_phase = provider.decide_next_phase(current_phase, context, [])
        assert current_phase == "planning"  # Stay in planning
        
        # Second planning iteration - still no items (at limit)
        provider.increment_phase_iteration(current_phase)
        current_phase = provider.decide_next_phase(current_phase, context, [])
        assert current_phase == "synthesis"  # Forced to synthesis (no progress)
        
        # Verify planning was reset
        assert provider._iteration_state.get_count("planning") == 0
        
        # Test successful planning -> allocation flow
        provider = OrchestratorPhaseProvider(
            iteration_limits=custom_limits,
            **mock_dependencies
        )
        
        current_phase = "planning"
        
        # Planning creates items
        status_with_items = create_work_plan_status(
            total_items=2,
            pending_items=2,
            has_local_ready=False,
            is_complete=False
        )
        context_with_items = create_phase_state(work_plan_status=status_with_items)
        
        provider.increment_phase_iteration(current_phase)
        current_phase = provider.decide_next_phase(current_phase, context_with_items, [])
        assert current_phase == "allocation"  # Normal transition
        
        # Allocation phase
        for i in range(3):  # Allocation limit is 3
            provider.increment_phase_iteration(current_phase)
            if i < 2:  # Not at limit yet
                next_phase = provider.decide_next_phase(current_phase, context_with_items, [])
                assert next_phase == "allocation"  # Stay in allocation
            else:  # At limit
                next_phase = provider.decide_next_phase(current_phase, context_with_items, [])
                assert next_phase == "monitoring"  # Forced transition
        
        # Verify allocation was reset
        assert provider._iteration_state.get_count("allocation") == 0
