"""
Temporal workflow — inbound adapter (thin SDK wrapper).

Defines the @workflow.defn for Temporal registration.
Delegates graph traversal logic to engine.distributed.traversal.GraphTraversal.
Activity calls remain explicit here (Temporal requires direct await on
workflow.execute_activity for deterministic replay).
"""
from datetime import timedelta
from typing import Any, Dict, List

from temporalio import workflow
from temporalio.common import RetryPolicy

from mas.engine.domain.models import GraphDefinition, ConditionalEdgeDef
from mas.engine.distributed.traversal import GraphTraversal
from mas.graph.state.graph_state import GraphState
from outbound.temporal.models import (
    GraphExecutionParams,
    ExecuteNodeParams,
    EvaluateConditionParams,
)

_NODE_TIMEOUT = timedelta(minutes=15)
_NODE_HEARTBEAT = timedelta(minutes=10)
_NODE_RETRY = RetryPolicy(maximum_attempts=3)

_CONDITION_TIMEOUT = timedelta(seconds=30)
_CONDITION_RETRY = RetryPolicy(maximum_attempts=2)


@workflow.defn
class GraphTraversalWorkflow:
    """
    Thin Temporal workflow that wires activity calls into the
    engine-level GraphTraversal algorithm.
    """

    def __init__(self) -> None:
        self._state: Dict[str, Any] = {}
        self._current_nodes: List[str] = []
        self._session_id: str = ""

    @workflow.run
    async def run(self, params: GraphExecutionParams) -> dict:
        graph = GraphDefinition.model_validate(params.graph_definition)
        state = GraphState.deserialize(params.state)
        self._session_id = params.session_id

        traversal = GraphTraversal(graph, GraphState)

        final_state = await traversal.run(
            initial_state=state,
            execute_node=self._execute_node,
            evaluate_condition=self._evaluate_condition,
            on_superstep=self._on_superstep,
        )

        self._state = final_state.serialize()
        self._current_nodes = []
        return self._state

    @workflow.query
    def get_state(self) -> dict:
        return self._state

    @workflow.query
    def get_current_nodes(self) -> List[str]:
        return self._current_nodes

    def _on_superstep(self, step, active_nodes, serialized_state):
        self._current_nodes = sorted(active_nodes)
        self._state = serialized_state

    async def _execute_node(
        self,
        uid: str,
        state: GraphState,
        graph: GraphDefinition,
    ) -> GraphState:
        node_def = graph.nodes[uid]
        params = ExecuteNodeParams(
            node_uid=uid,
            node_blueprint=node_def.node_blueprint,
            step_context=node_def.step_context,
            state=state.serialize(),
            session_id=self._session_id,
        )
        result_dict = await workflow.execute_activity(
            "execute_graph_node",
            params,
            start_to_close_timeout=_NODE_TIMEOUT,
            heartbeat_timeout=_NODE_HEARTBEAT,
            retry_policy=_NODE_RETRY,
        )
        return GraphState.deserialize(result_dict)

    async def _evaluate_condition(
        self,
        state: GraphState,
        cond: ConditionalEdgeDef,
    ) -> str:
        params = EvaluateConditionParams(
            condition_rid=cond.condition_rid,
            condition_blueprint=cond.condition_blueprint,
            step_context=cond.step_context,
            state=state.serialize(),
        )
        return await workflow.execute_activity(
            "evaluate_condition",
            params,
            start_to_close_timeout=_CONDITION_TIMEOUT,
            retry_policy=_CONDITION_RETRY,
        )
