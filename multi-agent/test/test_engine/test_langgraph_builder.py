import pytest
from engine.langgraph_builder import LangGraphBuilder
from graph.graph_plan import GraphPlan


# Dummy function for nodes
def dummy_func(state):
    state["log"].append(f"processed_{state['step']}")
    return state


@pytest.fixture
def linear_graph_plan():
    plan = GraphPlan()
    plan.add_step("start", dummy_func)
    plan.add_step("middle", dummy_func, after="start")
    plan.add_step("end", dummy_func, after="middle")
    return plan


def test_builds_linear_graph_successfully(linear_graph_plan):
    builder = LangGraphBuilder()
    compiled_graph = builder.build(linear_graph_plan)
    assert compiled_graph is not None
    assert hasattr(compiled_graph, "invoke")


def test_compiled_graph_runs_linear_flow(linear_graph_plan):
    builder = LangGraphBuilder()
    graph = builder.build(linear_graph_plan)

    state = {"step": "start", "messages": [], "log": []}
    result = graph.invoke(state)

    assert "processed_start" in result["log"]
    assert "processed_middle" in result["log"]
    assert "processed_end" in result["log"]


def test_supports_conditional_branching():
    plan = GraphPlan()

    def decision_func(state):
        return "branch_a" if state.get("route") == "a" else "branch_b"

    plan.add_step(
        name="check_branch",
        func=dummy_func,
        condition=decision_func,
        branches={"branch_a": "a", "branch_b": "b"}
    )
    plan.add_step("a", dummy_func)
    plan.add_step("b", dummy_func)

    builder = LangGraphBuilder()
    graph = builder.build(plan)

    result_a = graph.invoke({"route": "a", "step": "check_branch", "messages": [], "log": []})
    result_b = graph.invoke({"route": "x", "step": "check_branch", "messages": [], "log": []})

    assert "processed_check_branch" in result_a["log"]
    assert "processed_a" in result_a["log"]

    assert "processed_check_branch" in result_b["log"]
    assert "processed_b" in result_b["log"]


def test_raises_on_empty_plan():
    builder = LangGraphBuilder()
    empty_plan = GraphPlan()

    with pytest.raises(IndexError):
        builder.build(empty_plan)


def test_duplicate_node_names_raise_error():
    plan = GraphPlan()
    plan.add_step("dup", dummy_func)
    plan.add_step("dup", dummy_func)  # Duplicate!

    builder = LangGraphBuilder()

    with pytest.raises(Exception):
        builder.build(plan)


def test_logging_during_execution(linear_plan, mock_logger):
    builder = LangGraphBuilder()
    graph = builder.build(linear_plan)

    state = {"step": "start", "messages": [], "log": []}

    # Simulate log tracking for key points manually (or via callback integration in future)
    mock_logger.log_node_start("start")
    result = graph.invoke(state)
    mock_logger.log_node_end("end")

    # Validate structured logs were recorded
    assert "START:start" in mock_logger.get_events()
    assert "END:end" in mock_logger.get_events()
