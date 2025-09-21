"""
Unit tests for PlanAndExecuteStrategy.

Tests the core strategy functionality including phase transitions,
tool filtering, context provision, and all edge cases.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import List, Dict, Any

from elements.nodes.common.agent.strategies.plan_execute import PlanAndExecuteStrategy
from elements.nodes.common.agent.constants import ExecutionPhase
from elements.nodes.common.agent.phase_protocols import (
    PhaseContextProvider, PhaseToolProvider, PhaseTransitionPolicy,
    PhaseState, WorkPlanStatus, create_work_plan_status, create_phase_state
)
from elements.nodes.common.agent.primitives import AgentObservation
from elements.tools.common.base_tool import BaseTool


class MockTool(BaseTool):
    """Mock tool for testing."""
    
    def __init__(self, name: str, description: str = "Mock tool"):
        self.name = name
        self.description = description
        self.args_schema = None
    
    def run(self, **kwargs):
        return {"success": True, "result": f"Mock result from {self.name}"}


class MockPhaseContextProvider(PhaseContextProvider):
    """Mock phase context provider for testing."""
    
    def __init__(self, work_plan_status: WorkPlanStatus = None):
        self.work_plan_status = work_plan_status or create_work_plan_status()
        self.call_count = 0
    
    def get_phase_context(self) -> PhaseState:
        self.call_count += 1
        return create_phase_state(
            work_plan_status=self.work_plan_status,
            thread_id="test-thread",
            node_uid="test-node"
        )
    
    def update_status(self, **kwargs):
        """Helper to update status for testing."""
        self.work_plan_status = create_work_plan_status(**kwargs)


class MockPhaseToolProvider(PhaseToolProvider):
    """Mock phase tool provider for testing."""
    
    def __init__(self, phase_tools: Dict[ExecutionPhase, List[BaseTool]] = None):
        self.phase_tools = phase_tools or {}
        self.call_count = 0
    
    def get_tools_for_phase(self, phase: ExecutionPhase) -> List[BaseTool]:
        self.call_count += 1
        return self.phase_tools.get(phase, [])
    
    def get_all_phase_tools(self) -> Dict[ExecutionPhase, List[BaseTool]]:
        return self.phase_tools.copy()


class MockPhaseTransitionPolicy(PhaseTransitionPolicy):
    """Mock phase transition policy for testing."""
    
    def __init__(self, transitions: Dict[ExecutionPhase, ExecutionPhase] = None):
        self.transitions = transitions or {}
        self.call_count = 0
        self.last_state = None
        self.last_current = None
        self.last_observations = None
    
    def decide(self, *, state: PhaseState, current: ExecutionPhase, observations: List['AgentObservation']) -> ExecutionPhase:
        self.call_count += 1
        self.last_state = state
        self.last_current = current
        self.last_observations = observations
        return self.transitions.get(current, current)


class TestPlanAndExecuteStrategyInitialization:
    """Test strategy initialization and configuration."""
    
    def test_basic_initialization(self):
        """Test basic strategy initialization."""
        tools = [MockTool("test_tool")]
        strategy = PlanAndExecuteStrategy(tools=tools)
        
        assert strategy._current_phase == ExecutionPhase.PLANNING
        assert len(strategy.all_tools) == 1
        assert "test_tool" in strategy.all_tools
        assert strategy._phase_tool_provider is None
        assert strategy._phase_context_provider is None
        assert strategy._phase_transition_policy is None
    
    def test_initialization_with_providers(self):
        """Test initialization with all providers."""
        tools = [MockTool("test_tool")]
        context_provider = MockPhaseContextProvider()
        tool_provider = MockPhaseToolProvider()
        transition_policy = MockPhaseTransitionPolicy()
        
        strategy = PlanAndExecuteStrategy(
            tools=tools,
            phase_context_provider=context_provider,
            phase_tool_provider=tool_provider,
            phase_transition_policy=transition_policy
        )
        
        assert strategy._phase_context_provider is context_provider
        assert strategy._phase_tool_provider is tool_provider
        assert strategy._phase_transition_policy is transition_policy
    
    def test_initialization_with_system_message(self):
        """Test initialization with system message."""
        tools = [MockTool("test_tool")]
        system_message = "You are a specialized orchestrator"
        
        strategy = PlanAndExecuteStrategy(
            tools=tools,
            system_message=system_message
        )
        
        assert strategy.system_message == system_message


class TestPlanAndExecuteStrategyPhaseManagement:
    """Test phase management and transitions."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.tools = [
            MockTool("planning_tool"),
            MockTool("allocation_tool"),
            MockTool("execution_tool"),
            MockTool("monitoring_tool"),
            MockTool("synthesis_tool")
        ]
        
        self.context_provider = MockPhaseContextProvider()
        self.tool_provider = MockPhaseToolProvider({
            ExecutionPhase.PLANNING: [self.tools[0]],
            ExecutionPhase.ALLOCATION: [self.tools[1]],
            ExecutionPhase.EXECUTION: [self.tools[2]],
            ExecutionPhase.MONITORING: [self.tools[3]],
            ExecutionPhase.SYNTHESIS: [self.tools[4]]
        })
        self.transition_policy = MockPhaseTransitionPolicy()
        
        self.strategy = PlanAndExecuteStrategy(
            tools=self.tools,
            phase_context_provider=self.context_provider,
            phase_tool_provider=self.tool_provider,
            phase_transition_policy=self.transition_policy
        )
    
    def test_get_current_phase(self):
        """Test getting current phase."""
        assert self.strategy.get_current_phase() == ExecutionPhase.PLANNING
        
        self.strategy._current_phase = ExecutionPhase.ALLOCATION
        assert self.strategy.get_current_phase() == ExecutionPhase.ALLOCATION
    
    def test_get_tools_for_phase_with_provider(self):
        """Test getting tools for phase with provider."""
        planning_tools = self.strategy.get_tools_for_phase(ExecutionPhase.PLANNING)
        
        assert len(planning_tools) == 1
        assert planning_tools[0].name == "planning_tool"
        assert self.tool_provider.call_count == 1
    
    def test_get_tools_for_phase_without_provider(self):
        """Test getting tools for phase without provider."""
        strategy = PlanAndExecuteStrategy(tools=self.tools)
        
        # Should return all tools when no provider
        planning_tools = strategy.get_tools_for_phase(ExecutionPhase.PLANNING)
        assert len(planning_tools) == 5
    
    def test_get_tools_for_phase_invalid_phase(self):
        """Test getting tools for invalid phase."""
        # Should handle invalid phase gracefully
        tools = self.strategy.get_tools_for_phase("invalid_phase")
        assert len(tools) == 5  # Falls back to all tools
    
    def test_update_phase_with_policy(self):
        """Test phase update with transition policy."""
        # Set up transition: PLANNING -> ALLOCATION
        self.transition_policy.transitions[ExecutionPhase.PLANNING] = ExecutionPhase.ALLOCATION
        
        observations = [Mock(spec=AgentObservation)]
        self.strategy._update_phase(observations)
        
        assert self.strategy._current_phase == ExecutionPhase.ALLOCATION
        assert self.transition_policy.call_count == 1
        assert self.transition_policy.last_current == ExecutionPhase.PLANNING
        assert self.transition_policy.last_observations == observations
    
    def test_update_phase_without_policy(self):
        """Test phase update without transition policy (fallback logic)."""
        strategy = PlanAndExecuteStrategy(tools=self.tools)
        
        # Should use built-in fallback logic
        observations = []
        strategy._update_phase(observations)
        
        # Should stay in PLANNING phase (no work plan status to change it)
        assert strategy._current_phase == ExecutionPhase.PLANNING
    
    def test_update_phase_policy_error_fallback(self):
        """Test phase update falls back when policy raises error."""
        # Make policy raise exception
        def failing_decide(**kwargs):
            raise Exception("Policy error")
        
        self.transition_policy.decide = failing_decide
        
        observations = []
        self.strategy._update_phase(observations)
        
        # Should fall back to built-in logic and stay in PLANNING
        assert self.strategy._current_phase == ExecutionPhase.PLANNING


class TestPlanAndExecuteStrategyWorkPlanStatus:
    """Test work plan status retrieval and handling."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.tools = [MockTool("test_tool")]
        self.context_provider = MockPhaseContextProvider()
        self.strategy = PlanAndExecuteStrategy(
            tools=self.tools,
            phase_context_provider=self.context_provider
        )
    
    def test_get_work_plan_status_with_provider(self):
        """Test getting work plan status with provider."""
        # Set up status
        self.context_provider.update_status(
            total_items=5,
            pending_items=2,
            done_items=3,
            is_complete=False
        )
        
        status = self.strategy._get_work_plan_status()
        
        assert status is not None
        assert status.total_items == 5
        assert status.pending_items == 2
        assert status.done_items == 3
        assert status.is_complete is False
        assert self.context_provider.call_count == 1
    
    def test_get_work_plan_status_without_provider(self):
        """Test getting work plan status without provider."""
        strategy = PlanAndExecuteStrategy(tools=self.tools)
        
        status = strategy._get_work_plan_status()
        assert status is None
    
    def test_get_work_plan_status_provider_error(self):
        """Test getting work plan status when provider raises error."""
        def failing_get_context():
            raise Exception("Context provider error")
        
        self.context_provider.get_phase_context = failing_get_context
        
        status = self.strategy._get_work_plan_status()
        assert status is None


class TestPlanAndExecuteStrategyBuiltinPhaseLogic:
    """Test built-in phase transition logic."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.tools = [MockTool("test_tool")]
        self.context_provider = MockPhaseContextProvider()
        self.strategy = PlanAndExecuteStrategy(
            tools=self.tools,
            phase_context_provider=self.context_provider
        )
    
    def test_builtin_logic_no_plan_goes_to_planning(self):
        """Test that no plan goes to planning phase."""
        # No work plan status (None)
        self.context_provider.update_status()  # Empty status
        
        observations = []
        self.strategy._update_phase(observations)
        
        assert self.strategy._current_phase == ExecutionPhase.PLANNING
    
    def test_builtin_logic_empty_plan_goes_to_planning(self):
        """Test that empty plan goes to planning phase."""
        self.context_provider.update_status(total_items=0)
        
        observations = []
        self.strategy._update_phase(observations)
        
        assert self.strategy._current_phase == ExecutionPhase.PLANNING
    
    def test_builtin_logic_complete_plan_goes_to_synthesis(self):
        """Test that complete plan goes to synthesis phase."""
        self.context_provider.update_status(
            total_items=3,
            done_items=2,
            failed_items=1,
            is_complete=True
        )
        
        observations = []
        self.strategy._update_phase(observations)
        
        assert self.strategy._current_phase == ExecutionPhase.SYNTHESIS
    
    def test_builtin_logic_pending_items_go_to_allocation(self):
        """Test that pending items go to allocation phase."""
        self.context_provider.update_status(
            total_items=5,
            pending_items=2,
            done_items=3,
            is_complete=False
        )
        
        observations = []
        self.strategy._update_phase(observations)
        
        assert self.strategy._current_phase == ExecutionPhase.ALLOCATION
    
    def test_builtin_logic_local_ready_goes_to_execution(self):
        """Test that local ready items go to execution phase."""
        self.context_provider.update_status(
            total_items=3,
            pending_items=0,
            has_local_ready=True,
            is_complete=False
        )
        
        observations = []
        self.strategy._update_phase(observations)
        
        assert self.strategy._current_phase == ExecutionPhase.EXECUTION
    
    def test_builtin_logic_in_progress_goes_to_monitoring(self):
        """Test that in-progress items go to monitoring phase."""
        self.context_provider.update_status(
            total_items=3,
            pending_items=0,
            in_progress_items=2,
            has_local_ready=False,
            is_complete=False
        )
        
        observations = []
        self.strategy._update_phase(observations)
        
        assert self.strategy._current_phase == ExecutionPhase.MONITORING
    
    def test_builtin_logic_waiting_goes_to_monitoring(self):
        """Test that waiting items go to monitoring phase."""
        self.context_provider.update_status(
            total_items=3,
            pending_items=0,
            waiting_items=2,
            has_local_ready=False,
            is_complete=False
        )
        
        observations = []
        self.strategy._update_phase(observations)
        
        assert self.strategy._current_phase == ExecutionPhase.MONITORING
    
    def test_builtin_logic_remote_waiting_goes_to_monitoring(self):
        """Test that remote waiting items go to monitoring phase."""
        self.context_provider.update_status(
            total_items=3,
            pending_items=0,
            has_local_ready=False,
            has_remote_waiting=True,
            is_complete=False
        )
        
        observations = []
        self.strategy._update_phase(observations)
        
        assert self.strategy._current_phase == ExecutionPhase.MONITORING
    
    def test_builtin_logic_priority_order(self):
        """Test that phase decisions follow correct priority order."""
        # Complete takes priority over everything
        self.context_provider.update_status(
            total_items=5,
            pending_items=2,  # Would normally go to allocation
            has_local_ready=True,  # Would normally go to execution
            is_complete=True  # But this takes priority
        )
        
        observations = []
        self.strategy._update_phase(observations)
        
        assert self.strategy._current_phase == ExecutionPhase.SYNTHESIS
        
        # Pending takes priority over local ready
        self.context_provider.update_status(
            total_items=5,
            pending_items=2,  # This takes priority
            has_local_ready=True,  # Over this
            is_complete=False
        )
        
        observations = []
        self.strategy._update_phase(observations)
        
        assert self.strategy._current_phase == ExecutionPhase.ALLOCATION


class TestPlanAndExecuteStrategyExecution:
    """Test strategy execution flow."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.tools = [
            MockTool("planning_tool"),
            MockTool("allocation_tool")
        ]
        
        self.context_provider = MockPhaseContextProvider()
        self.tool_provider = MockPhaseToolProvider({
            ExecutionPhase.PLANNING: [self.tools[0]],
            ExecutionPhase.ALLOCATION: [self.tools[1]]
        })
        
        self.strategy = PlanAndExecuteStrategy(
            tools=self.tools,
            phase_context_provider=self.context_provider,
            phase_tool_provider=self.tool_provider
        )
    
    def test_step_execution_basic(self):
        """Test basic step execution."""
        # Mock the agent execution
        with patch.object(self.strategy, '_execute_step') as mock_execute:
            mock_execute.return_value = Mock(
                observations=[Mock(spec=AgentObservation)],
                is_complete=False
            )
            
            result = self.strategy.step()
            
            assert mock_execute.called
            assert result is not None
    
    def test_step_execution_with_phase_transition(self):
        """Test step execution with phase transition."""
        # Set up transition policy
        transition_policy = MockPhaseTransitionPolicy({
            ExecutionPhase.PLANNING: ExecutionPhase.ALLOCATION
        })
        
        self.strategy._phase_transition_policy = transition_policy
        
        with patch.object(self.strategy, '_execute_step') as mock_execute:
            mock_execute.return_value = Mock(
                observations=[Mock(spec=AgentObservation)],
                is_complete=False
            )
            
            # Should start in PLANNING
            assert self.strategy._current_phase == ExecutionPhase.PLANNING
            
            result = self.strategy.step()
            
            # Should transition to ALLOCATION
            assert self.strategy._current_phase == ExecutionPhase.ALLOCATION
            assert transition_policy.call_count == 1
    
    def test_get_phase_specific_tools(self):
        """Test getting phase-specific tools during execution."""
        # Should get planning tools initially
        tools = self.strategy.get_tools_for_phase(ExecutionPhase.PLANNING)
        assert len(tools) == 1
        assert tools[0].name == "planning_tool"
        
        # Should get allocation tools for allocation phase
        tools = self.strategy.get_tools_for_phase(ExecutionPhase.ALLOCATION)
        assert len(tools) == 1
        assert tools[0].name == "allocation_tool"
    
    def test_context_provider_integration(self):
        """Test integration with context provider."""
        # Update context
        self.context_provider.update_status(
            total_items=3,
            pending_items=1,
            done_items=2
        )
        
        # Get status through strategy
        status = self.strategy._get_work_plan_status()
        
        assert status.total_items == 3
        assert status.pending_items == 1
        assert status.done_items == 2


class TestPlanAndExecuteStrategyEdgeCases:
    """Test edge cases and error scenarios."""
    
    def test_invalid_phase_enum(self):
        """Test handling of invalid phase enum values."""
        tools = [MockTool("test_tool")]
        tool_provider = MockPhaseToolProvider()
        
        strategy = PlanAndExecuteStrategy(
            tools=tools,
            phase_tool_provider=tool_provider
        )
        
        # Should handle invalid phase gracefully
        tools_result = strategy.get_tools_for_phase("invalid_phase")
        assert len(tools_result) == 1  # Falls back to all tools
    
    def test_none_providers(self):
        """Test handling of None providers."""
        tools = [MockTool("test_tool")]
        strategy = PlanAndExecuteStrategy(tools=tools)
        
        # Should handle None providers gracefully
        status = strategy._get_work_plan_status()
        assert status is None
        
        tools_result = strategy.get_tools_for_phase(ExecutionPhase.PLANNING)
        assert len(tools_result) == 1  # All tools
    
    def test_empty_tools_list(self):
        """Test handling of empty tools list."""
        strategy = PlanAndExecuteStrategy(tools=[])
        
        assert len(strategy.all_tools) == 0
        
        tools_result = strategy.get_tools_for_phase(ExecutionPhase.PLANNING)
        assert len(tools_result) == 0
    
    def test_context_provider_exception_handling(self):
        """Test handling of context provider exceptions."""
        tools = [MockTool("test_tool")]
        
        def failing_provider():
            raise Exception("Context provider failed")
        
        context_provider = Mock()
        context_provider.get_phase_context = failing_provider
        
        strategy = PlanAndExecuteStrategy(
            tools=tools,
            phase_context_provider=context_provider
        )
        
        # Should handle exception gracefully
        status = strategy._get_work_plan_status()
        assert status is None
    
    def test_tool_provider_exception_handling(self):
        """Test handling of tool provider exceptions."""
        tools = [MockTool("test_tool")]
        
        def failing_provider(phase):
            raise Exception("Tool provider failed")
        
        tool_provider = Mock()
        tool_provider.get_tools_for_phase = failing_provider
        
        strategy = PlanAndExecuteStrategy(
            tools=tools,
            phase_tool_provider=tool_provider
        )
        
        # Should fall back to all tools
        tools_result = strategy.get_tools_for_phase(ExecutionPhase.PLANNING)
        assert len(tools_result) == 1  # Falls back to all tools
    
    def test_transition_policy_exception_handling(self):
        """Test handling of transition policy exceptions."""
        tools = [MockTool("test_tool")]
        context_provider = MockPhaseContextProvider()
        
        def failing_policy(**kwargs):
            raise Exception("Transition policy failed")
        
        transition_policy = Mock()
        transition_policy.decide = failing_policy
        
        strategy = PlanAndExecuteStrategy(
            tools=tools,
            phase_context_provider=context_provider,
            phase_transition_policy=transition_policy
        )
        
        # Should fall back to built-in logic
        observations = []
        strategy._update_phase(observations)
        
        # Should stay in PLANNING (built-in logic with no work plan)
        assert strategy._current_phase == ExecutionPhase.PLANNING


class TestPlanAndExecuteStrategyIntegration:
    """Test integration scenarios with all components."""
    
    def test_full_integration_scenario(self):
        """Test full integration with all providers."""
        # Set up complete scenario
        tools = [
            MockTool("create_plan"),
            MockTool("assign_work"),
            MockTool("delegate_task"),
            MockTool("monitor_progress"),
            MockTool("summarize_results")
        ]
        
        context_provider = MockPhaseContextProvider()
        tool_provider = MockPhaseToolProvider({
            ExecutionPhase.PLANNING: [tools[0]],
            ExecutionPhase.ALLOCATION: [tools[1], tools[2]],
            ExecutionPhase.MONITORING: [tools[3]],
            ExecutionPhase.SYNTHESIS: [tools[4]]
        })
        
        # Set up phase transitions: PLANNING -> ALLOCATION -> MONITORING -> SYNTHESIS
        transition_policy = MockPhaseTransitionPolicy({
            ExecutionPhase.PLANNING: ExecutionPhase.ALLOCATION,
            ExecutionPhase.ALLOCATION: ExecutionPhase.MONITORING,
            ExecutionPhase.MONITORING: ExecutionPhase.SYNTHESIS
        })
        
        strategy = PlanAndExecuteStrategy(
            tools=tools,
            phase_context_provider=context_provider,
            phase_tool_provider=tool_provider,
            phase_transition_policy=transition_policy
        )
        
        # Simulate phase progression
        assert strategy._current_phase == ExecutionPhase.PLANNING
        
        # Get tools for current phase
        planning_tools = strategy.get_tools_for_phase(strategy._current_phase)
        assert len(planning_tools) == 1
        assert planning_tools[0].name == "create_plan"
        
        # Simulate phase transition
        observations = [Mock(spec=AgentObservation)]
        strategy._update_phase(observations)
        assert strategy._current_phase == ExecutionPhase.ALLOCATION
        
        # Get tools for new phase
        allocation_tools = strategy.get_tools_for_phase(strategy._current_phase)
        assert len(allocation_tools) == 2
        tool_names = {tool.name for tool in allocation_tools}
        assert "assign_work" in tool_names
        assert "delegate_task" in tool_names
        
        # Continue transitions
        strategy._update_phase(observations)
        assert strategy._current_phase == ExecutionPhase.MONITORING
        
        strategy._update_phase(observations)
        assert strategy._current_phase == ExecutionPhase.SYNTHESIS
        
        # Verify all providers were called
        assert context_provider.call_count >= 3  # Called during transitions
        assert tool_provider.call_count >= 4  # Called for each phase
        assert transition_policy.call_count == 3  # Called for each transition
    
    def test_realistic_work_plan_progression(self):
        """Test realistic work plan status progression."""
        tools = [MockTool("test_tool")]
        context_provider = MockPhaseContextProvider()
        
        strategy = PlanAndExecuteStrategy(
            tools=tools,
            phase_context_provider=context_provider
        )
        
        # 1. Start with no plan - should go to PLANNING
        context_provider.update_status(total_items=0)
        strategy._update_phase([])
        assert strategy._current_phase == ExecutionPhase.PLANNING
        
        # 2. Plan created with pending items - should go to ALLOCATION
        context_provider.update_status(
            total_items=3,
            pending_items=3,
            is_complete=False
        )
        strategy._update_phase([])
        assert strategy._current_phase == ExecutionPhase.ALLOCATION
        
        # 3. Items assigned and delegated - should go to MONITORING
        context_provider.update_status(
            total_items=3,
            pending_items=0,
            waiting_items=3,
            has_remote_waiting=True,
            is_complete=False
        )
        strategy._update_phase([])
        assert strategy._current_phase == ExecutionPhase.MONITORING
        
        # 4. Some items complete, some still waiting - stay in MONITORING
        context_provider.update_status(
            total_items=3,
            pending_items=0,
            waiting_items=1,
            done_items=2,
            has_remote_waiting=True,
            is_complete=False
        )
        strategy._update_phase([])
        assert strategy._current_phase == ExecutionPhase.MONITORING
        
        # 5. All items complete - should go to SYNTHESIS
        context_provider.update_status(
            total_items=3,
            pending_items=0,
            waiting_items=0,
            done_items=3,
            is_complete=True
        )
        strategy._update_phase([])
        assert strategy._current_phase == ExecutionPhase.SYNTHESIS
    
    def test_mixed_local_remote_scenario(self):
        """Test scenario with mixed local and remote work."""
        tools = [MockTool("test_tool")]
        context_provider = MockPhaseContextProvider()
        
        strategy = PlanAndExecuteStrategy(
            tools=tools,
            phase_context_provider=context_provider
        )
        
        # Plan with both local ready and remote waiting items
        context_provider.update_status(
            total_items=4,
            pending_items=1,  # One item still needs assignment
            has_local_ready=True,  # One local item ready
            has_remote_waiting=True,  # One remote item waiting
            done_items=1,  # One item already done
            is_complete=False
        )
        
        # Should prioritize pending items (ALLOCATION)
        strategy._update_phase([])
        assert strategy._current_phase == ExecutionPhase.ALLOCATION
        
        # After assignment, no pending but has local ready
        context_provider.update_status(
            total_items=4,
            pending_items=0,
            has_local_ready=True,
            has_remote_waiting=True,
            done_items=1,
            is_complete=False
        )
        
        # Should go to EXECUTION for local work
        strategy._update_phase([])
        assert strategy._current_phase == ExecutionPhase.EXECUTION
        
        # After local execution, only remote waiting
        context_provider.update_status(
            total_items=4,
            pending_items=0,
            has_local_ready=False,
            has_remote_waiting=True,
            done_items=2,
            is_complete=False
        )
        
        # Should go to MONITORING for remote work
        strategy._update_phase([])
        assert strategy._current_phase == ExecutionPhase.MONITORING


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

