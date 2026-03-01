"""
Temporal activity class for graph node execution.

Wraps node callables (from RTGraphPlan) as Temporal activity methods.
The class instance holds the live callables; the methods are registered
as activities on an embedded worker.  This mirrors how LangGraph's
compiled StateGraph holds callables — we just run them through Temporal.
"""
from typing import Callable, Dict

from temporalio import activity

from graph.state.graph_state import GraphState
from temporal.graph_models import ExecuteNodeParams, EvaluateConditionParams


class GraphNodeActivities:
    """
    Holds node and condition callables, exposes them as Temporal activities.

    Created by TemporalGraphBuilder from RTGraphPlan's bound callables.
    Registered on an embedded worker by TemporalGraphExecutor.

    The callables are the SAME objects that LangGraph would call directly —
    BaseNode instances with LLM, tools, and StepContext already injected.
    """

    def __init__(
            self,
            node_funcs: Dict[str, Callable],
            condition_funcs: Dict[str, Callable],
    ) -> None:
        self._nodes = node_funcs
        self._conditions = condition_funcs

    @activity.defn(name="execute_graph_node")
    def execute_node(self, params: ExecuteNodeParams) -> dict:
        """
        Run a single graph node.

        Retrieves the callable from self._nodes (injected at construction),
        deserializes the state, calls the node, and serializes the result.
        Exactly what LangGraph does in-process — just wrapped in an activity
        for retry, timeout, and observability.
        """
        func = self._nodes[params.node_uid]
        graph_state = GraphState.deserialize(params.state)

        activity.logger.info(f"Executing node: {params.node_uid}")
        result_state = func(graph_state, config={})

        return result_state.serialize()

    @activity.defn(name="evaluate_condition")
    def evaluate_condition(self, params: EvaluateConditionParams) -> str:
        """
        Evaluate a graph condition and return the branch key.

        Conditions are lightweight state readers (no LLM, no I/O).
        Run as activities so the workflow code stays deterministic.
        """
        func = self._conditions[params.condition_rid]
        graph_state = GraphState.deserialize(params.state)

        activity.logger.info(f"Evaluating condition: {params.condition_rid}")
        return func(graph_state)
