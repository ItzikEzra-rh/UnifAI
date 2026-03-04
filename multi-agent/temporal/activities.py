"""
Temporal activities — thin SDK wrappers.

Each @activity.defn method unpacks the DTO and delegates to
engine.temporal.node_executor.NodeExecutor for the actual
business logic (blueprint rebuilding, context injection, execution).
"""
from temporalio import activity

from engine.temporal.node_executor import NodeExecutor
from temporal.models import ExecuteNodeParams, EvaluateConditionParams


class GraphNodeActivities:
    """
    Stateless activity class for Temporal workers.

    Created once at worker startup. Each activity call delegates
    to NodeExecutor which builds a fresh node from the mini-blueprint.
    """

    def __init__(self, node_executor: NodeExecutor) -> None:
        self._executor = node_executor

    @activity.defn(name="execute_graph_node")
    def execute_node(self, params: ExecuteNodeParams) -> dict:
        activity.logger.info(f"Executing node: {params.node_uid}")
        return self._executor.execute_node(
            node_uid=params.node_uid,
            node_blueprint=params.node_blueprint,
            step_context=params.step_context,
            state=params.state,
        )

    @activity.defn(name="evaluate_condition")
    def evaluate_condition(self, params: EvaluateConditionParams) -> str:
        activity.logger.info(f"Evaluating condition: {params.condition_rid}")
        return self._executor.evaluate_condition(
            condition_rid=params.condition_rid,
            condition_blueprint=params.condition_blueprint,
            step_context=params.step_context,
            state=params.state,
        )
