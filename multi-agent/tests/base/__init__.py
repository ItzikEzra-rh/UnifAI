"""
Base test infrastructure.

Exports base test classes and helper functions for reuse across all tests.
All helpers here are GENERIC and work for ANY node type.
"""

from tests.base.base_node_test import BaseNodeTest, BaseOrchestratorTest, BaseCustomAgentTest
from tests.base.base_integration_test import BaseIntegrationTest
from tests.base.base_unit_test import BaseUnitTest
from tests.base.test_helpers import (
    create_test_step_context,
    setup_node_with_state,
    setup_node_with_context,
    assert_workplan_created,
    assert_has_workload_capability,
    assert_has_iem_capability,
    assert_has_llm_capability,
    assert_has_agent_capability,
    get_workspace_from_node,
    # Orchestration helpers
    create_work_plan_with_items,
    assert_work_plan_status,
    create_mock_worker_node,
    simulate_worker_response,
    create_predictable_llm_for_phases,
    # Thread hierarchy helpers
    create_thread_hierarchy,
    create_multi_level_hierarchy,
    assert_thread_hierarchy,
    assert_response_routes_to_root,
    get_hierarchy_depth,
)

__all__ = [
    # Base test classes
    'BaseNodeTest',
    'BaseOrchestratorTest', 
    'BaseCustomAgentTest',
    'BaseIntegrationTest',
    'BaseUnitTest',
    
    # GENERIC helper functions (work for ALL nodes)
    'create_test_step_context',
    'setup_node_with_state',
    'setup_node_with_context',
    'assert_workplan_created',
    'assert_has_workload_capability',
    'assert_has_iem_capability',
    'assert_has_llm_capability',
    'assert_has_agent_capability',
    'get_workspace_from_node',
    
    # GENERIC orchestration helpers
    'create_work_plan_with_items',
    'assert_work_plan_status',
    'create_mock_worker_node',
    'simulate_worker_response',
    'create_predictable_llm_for_phases',
    # Thread Hierarchy Helpers
    'create_thread_hierarchy',
    'create_multi_level_hierarchy',
    'assert_thread_hierarchy',
    'assert_response_routes_to_root',
    'get_hierarchy_depth',
]