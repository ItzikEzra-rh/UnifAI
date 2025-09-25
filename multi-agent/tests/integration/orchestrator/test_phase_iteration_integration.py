"""
Integration tests for phase iteration limits with strategy integration.

Tests the complete flow from strategy -> phase provider -> iteration tracking
to ensure infinite loops are prevented in realistic scenarios.
"""

import pytest
from unittest.mock import Mock, patch

from elements.nodes.orchestrator.phases.models import PhaseIterationLimits, PhaseIterationState
from elements.nodes.orchestrator.orchestrator_phase_provider import OrchestratorPhaseProvider
from elements.nodes.common.agent.strategies.plan_execute import PlanAndExecuteStrategy
from elements.nodes.common.agent.primitives import AgentObservation
from elements.nodes.common.agent.phases.phase_protocols import create_phase_state, create_work_plan_status
from elements.llms.common.chat.message import ChatMessage, Role


class TestPhaseIterationStrategyIntegration:
    """Test phase iteration limits integration with PlanAndExecuteStrategy."""
    
    @pytest.fixture
    def mock_llm_chat(self):
        """Mock LLM chat function."""
        def mock_chat(messages, tools):
            # Return a simple response that doesn't do much
            return ChatMessage(
                role=Role.ASSISTANT,
                content="I'll work on this task step by step."
            )
        return mock_chat
    
    @pytest.fixture
    def mock_parser(self):
        """Mock output parser."""
        parser = Mock()
        parser.parse.return_value = []  # No steps parsed
        return parser
    
    @pytest.fixture
    def phase_provider_with_low_limits(self):
        """Create phase provider with very low limits for testing."""
        custom_limits = PhaseIterationLimits(
            planning=2, allocation=2, execution=2, monitoring=2, synthesis=1
        )
        
        mock_dependencies = {
            'domain_tools': [],
            'get_adjacent_nodes': Mock(return_value={}),
            'send_task': Mock(),
            'node_uid': 'test_orchestrator',
            'thread_id': 'test_thread',
            'get_workload_service': Mock()
        }
        
        return OrchestratorPhaseProvider(
            iteration_limits=custom_limits,
            **mock_dependencies
        )
    
    def test_strategy_calls_increment_phase_iteration(self, mock_llm_chat, mock_parser, phase_provider_with_low_limits):
        """Test that strategy properly calls increment_phase_iteration."""
        strategy = PlanAndExecuteStrategy(
            llm_chat=mock_llm_chat,
            tools=[],
            parser=mock_parser,
            max_steps=10,
            phase_provider=phase_provider_with_low_limits
        )
        
        # Mock the phase context to return empty work plan
        with patch.object(phase_provider_with_low_limits, 'get_phase_context') as mock_context:
            mock_context.return_value = create_phase_state(
                work_plan_status=create_work_plan_status(
                    total_items=0,
                    is_complete=False
                )
            )
            
            # Initial state - no iterations
            assert phase_provider_with_low_limits._iteration_state.get_count("planning") == 0
            
            # Simulate strategy calling _update_phase
            observations = []
            strategy._update_phase(observations)
            
            # Should increment planning iteration
            assert phase_provider_with_low_limits._iteration_state.get_count("planning") == 1
    
    def test_strategy_respects_phase_limits(self, mock_llm_chat, mock_parser, phase_provider_with_low_limits):
        """Test that strategy respects phase limits and transitions appropriately."""
        strategy = PlanAndExecuteStrategy(
            llm_chat=mock_llm_chat,
            tools=[],
            parser=mock_parser,
            max_steps=10,
            phase_provider=phase_provider_with_low_limits
        )
        
        # Mock phase context to simulate stuck planning phase
        with patch.object(phase_provider_with_low_limits, 'get_phase_context') as mock_context:
            # No work items created (stuck in planning)
            mock_context.return_value = create_phase_state(
                work_plan_status=create_work_plan_status(
                    total_items=0,
                    is_complete=False
                )
            )
            
            # Start in planning
            assert strategy._current_phase == "planning"
            
            # First iteration - should stay in planning (count=1, under limit of 2)
            strategy._update_phase([])
            assert strategy._current_phase == "planning"
            assert phase_provider_with_low_limits._iteration_state.get_count("planning") == 1
            
            # Second iteration - should transition to synthesis (count=2, at limit of 2)
            strategy._update_phase([])
            assert strategy._current_phase == "synthesis"  # Forced transition at limit
            assert phase_provider_with_low_limits._iteration_state.get_count("planning") == 0  # Reset
    
    def test_strategy_normal_progression_with_limits(self, mock_llm_chat, mock_parser, phase_provider_with_low_limits):
        """Test normal phase progression when limits are not exceeded."""
        strategy = PlanAndExecuteStrategy(
            llm_chat=mock_llm_chat,
            tools=[],
            parser=mock_parser,
            max_steps=10,
            phase_provider=phase_provider_with_low_limits
        )
        
        # Mock phase context to simulate successful progression
        contexts = [
            # Planning creates work items
            create_phase_state(
                work_plan_status=create_work_plan_status(
                    total_items=2,
                    pending_items=2,
                    has_local_ready=False,
                    is_complete=False
                )
            ),
            # Allocation assigns items
            create_phase_state(
                work_plan_status=create_work_plan_status(
                    total_items=2,
                    pending_items=0,
                    has_local_ready=True,
                    is_complete=False
                )
            ),
            # Execution completes work
            create_phase_state(
                work_plan_status=create_work_plan_status(
                    total_items=2,
                    pending_items=0,
                    has_local_ready=False,
                    is_complete=True
                )
            )
        ]
        
        context_iter = iter(contexts)
        
        with patch.object(phase_provider_with_low_limits, 'get_phase_context') as mock_context:
            def get_next_context():
                try:
                    return next(context_iter)
                except StopIteration:
                    return contexts[-1]  # Return last context
            
            mock_context.side_effect = get_next_context
            
            # Start in planning
            assert strategy._current_phase == "planning"
            
            # Planning -> Allocation (normal transition)
            strategy._update_phase([])
            assert strategy._current_phase == "allocation"
            assert phase_provider_with_low_limits._iteration_state.get_count("planning") == 0  # Reset
            
            # Allocation -> Execution (normal transition)
            strategy._update_phase([])
            assert strategy._current_phase == "execution"
            assert phase_provider_with_low_limits._iteration_state.get_count("allocation") == 0  # Reset
            
            # Execution -> Monitoring (normal transition)
            strategy._update_phase([])
            assert strategy._current_phase == "monitoring"
            assert phase_provider_with_low_limits._iteration_state.get_count("execution") == 0  # Reset
            
            # Monitoring -> Synthesis (work complete)
            strategy._update_phase([])
            assert strategy._current_phase == "synthesis"
            assert phase_provider_with_low_limits._iteration_state.get_count("monitoring") == 0  # Reset
    
    def test_allocation_phase_limit_with_fallback(self, mock_llm_chat, mock_parser, phase_provider_with_low_limits):
        """Test allocation phase limit exceeded with intelligent fallback to monitoring."""
        strategy = PlanAndExecuteStrategy(
            llm_chat=mock_llm_chat,
            tools=[],
            parser=mock_parser,
            max_steps=10,
            phase_provider=phase_provider_with_low_limits
        )
        
        # Start in allocation phase
        strategy._current_phase = "allocation"
        
        with patch.object(phase_provider_with_low_limits, 'get_phase_context') as mock_context:
            # Allocation phase with work that needs assignment (stuck allocation)
            mock_context.return_value = create_phase_state(
                work_plan_status=create_work_plan_status(
                    total_items=2,
                    pending_items=1,
                    has_local_ready=False,  # No work ready yet (still allocating)
                    has_remote_waiting=False,  # No remote work waiting either
                    is_complete=False
                )
            )
            
            # First allocation iteration (count=1, under limit of 2)
            strategy._update_phase([])
            assert strategy._current_phase == "allocation"
            assert phase_provider_with_low_limits._iteration_state.get_count("allocation") == 1
            
            # Second allocation iteration (count=2, at limit of 2) - should transition to monitoring
            strategy._update_phase([])
            assert strategy._current_phase == "monitoring"  # Smart fallback at limit (no local work ready)
            assert phase_provider_with_low_limits._iteration_state.get_count("allocation") == 0  # Reset
    
    def test_monitoring_phase_limit_force_synthesis(self, mock_llm_chat, mock_parser, phase_provider_with_low_limits):
        """Test monitoring phase limit exceeded forces synthesis."""
        strategy = PlanAndExecuteStrategy(
            llm_chat=mock_llm_chat,
            tools=[],
            parser=mock_parser,
            max_steps=10,
            phase_provider=phase_provider_with_low_limits
        )
        
        # Start in monitoring phase
        strategy._current_phase = "monitoring"
        
        with patch.object(phase_provider_with_low_limits, 'get_phase_context') as mock_context:
            # Monitoring phase waiting for responses (stuck)
            mock_context.return_value = create_phase_state(
                work_plan_status=create_work_plan_status(
                    total_items=2,
                    pending_items=0,        # No unassigned work
                    in_progress_items=1,    # Work delegated and waiting for response
                    waiting_items=1,        # Work delegated and waiting for response
                    has_local_ready=False,
                    is_complete=False  # Not complete yet
                )
            )
            
            # First monitoring iteration (count=1, under limit of 2)
            strategy._update_phase([])
            assert strategy._current_phase == "monitoring"
            assert phase_provider_with_low_limits._iteration_state.get_count("monitoring") == 1
            
            # Second monitoring iteration (count=2, at limit of 2) - should force synthesis
            strategy._update_phase([])
            assert strategy._current_phase == "synthesis"  # Forced terminal at limit
            assert phase_provider_with_low_limits._iteration_state.get_count("monitoring") == 0  # Reset


class TestPhaseIterationPerformance:
    """Test performance aspects of phase iteration tracking."""
    
    def test_many_iterations_performance(self):
        """Test that many iterations don't cause performance issues."""
        custom_limits = PhaseIterationLimits(planning=1000)  # High limit
        
        mock_dependencies = {
            'domain_tools': [],
            'get_adjacent_nodes': Mock(return_value={}),
            'send_task': Mock(),
            'node_uid': 'perf_test',
            'thread_id': 'perf_thread',
            'get_workload_service': Mock()
        }
        
        provider = OrchestratorPhaseProvider(
            iteration_limits=custom_limits,
            **mock_dependencies
        )
        
        # Many increments should be fast
        import time
        start_time = time.time()
        
        for i in range(500):
            provider.increment_phase_iteration("planning")
        
        end_time = time.time()
        
        # Should complete quickly (under 1 second for 500 iterations)
        assert end_time - start_time < 1.0
        assert provider._iteration_state.get_count("planning") == 500
        assert not provider.is_phase_limit_exceeded("planning")  # Under limit
    
    def test_immutable_state_memory_usage(self):
        """Test that immutable state updates don't cause memory leaks."""
        provider_state = PhaseIterationState()
        
        # Many state updates
        for i in range(100):
            provider_state = provider_state.increment("planning")
            provider_state = provider_state.reset("allocation")
        
        # Final state should be correct
        assert provider_state.get_count("planning") == 100
        assert provider_state.get_count("allocation") == 0


class TestPhaseIterationEdgeCases:
    """Test edge cases in phase iteration system."""
    
    def test_unknown_phase_names(self):
        """Test handling of unknown phase names."""
        limits = PhaseIterationLimits()
        state = PhaseIterationState()
        
        # Unknown phase should use defaults/not fail
        assert limits.get_limit("unknown_phase") == 10
        assert state.get_count("unknown_phase") == 0
        
        # Increment/reset unknown phase should not fail
        new_state = state.increment("unknown_phase")
        assert new_state.model_dump() == state.model_dump()  # No change
        
        reset_state = state.reset("unknown_phase")
        assert reset_state.model_dump() == state.model_dump()  # No change
    
    def test_zero_and_negative_context(self):
        """Test edge cases with zero items and edge conditions."""
        custom_limits = PhaseIterationLimits(planning=1)  # Very low limit
        
        mock_dependencies = {
            'domain_tools': [],
            'get_adjacent_nodes': Mock(return_value={}),
            'send_task': Mock(),
            'node_uid': 'edge_test',
            'thread_id': 'edge_thread',
            'get_workload_service': Mock()
        }
        
        provider = OrchestratorPhaseProvider(
            iteration_limits=custom_limits,
            **mock_dependencies
        )
        
        # Context with all zeros
        status = create_work_plan_status(
            total_items=0,
            pending_items=0,
            in_progress_items=0,
            waiting_items=0,
            done_items=0,
            failed_items=0,
            blocked_items=0,
            has_local_ready=False,
            has_remote_waiting=False,
            is_complete=False
        )
        context = create_phase_state(work_plan_status=status)
        
        # Should handle gracefully
        provider.increment_phase_iteration("planning")
        result = provider.decide_next_phase("planning", context, [])
        
        # Should transition to synthesis (terminal) when no progress possible
        assert result == "synthesis"
