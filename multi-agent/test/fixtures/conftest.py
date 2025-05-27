# test/fixtures/conftest.py

import pytest
from graph.graph_plan import GraphPlan
from .mock_logger import MockLogger


# --- Dummy Function for Graph Nodes ---
@pytest.fixture
def dummy_func():
    def fn(state):
        state.setdefault("log", []).append(f"processed_{state.get('step')}")
        return state

    return fn


# --- Linear GraphPlan Fixture ---
@pytest.fixture
def linear_plan(dummy_func):
    plan = GraphPlan()
    plan.add_step("start", dummy_func)
    plan.add_step("middle", dummy_func, after="start")
    plan.add_step("end", dummy_func, after="middle")
    return plan


# --- Conditional GraphPlan Fixture ---
@pytest.fixture
def conditional_plan(dummy_func):
    def decision(state):
        return "branch_a" if state.get("path") == "a" else "branch_b"

    plan = GraphPlan()
    plan.add_step("check", dummy_func, condition=decision, branches={"branch_a": "a", "branch_b": "b"})
    plan.add_step("a", dummy_func)
    plan.add_step("b", dummy_func)
    return plan


@pytest.fixture
def mock_logger():
    return MockLogger()
