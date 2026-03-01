"""
Temporal workflow that IS the graph engine.

Traverses the graph topology, executing each node as a Temporal activity.
Handles sequential chains, parallel fan-out, conditional routing, and
convergence joins — all with Temporal's built-in durability and retry.

This is the Temporal equivalent of LangGraph's compiled.invoke():
  LangGraph: for each node in order → call func(state) → apply reducers
  Temporal:  for each node in order → execute activity → apply merge strategies
"""
import asyncio
from datetime import timedelta
from typing import Any, Dict, List, Set

from temporalio import workflow
from temporalio.common import RetryPolicy

from engine.models import GraphDefinition
from graph.state.graph_state import GraphState
from graph.state.merge_applicator import MergeApplicator
from temporal.graph_models import (
    GraphExecutionParams,
    ExecuteNodeParams,
    EvaluateConditionParams,
)

# Activity timeouts
_NODE_TIMEOUT = timedelta(minutes=5)
_NODE_HEARTBEAT = timedelta(minutes=2)
_NODE_RETRY = RetryPolicy(maximum_attempts=3)

_CONDITION_TIMEOUT = timedelta(seconds=30)
_CONDITION_RETRY = RetryPolicy(maximum_attempts=2)


@workflow.defn
class GraphTraversalWorkflow:
    """
    Graph traversal engine implemented as a Temporal workflow.

    Algorithm:
      1. Start with the entry node.
      2. Execute all ready nodes (parallel if more than one).
      3. Apply merge strategies to reconcile state.
      4. Resolve successors (conditions + edges).
      5. Activate nodes whose ALL predecessors are done.
      6. Repeat until no nodes are ready.
    """

    def __init__(self) -> None:
        self._state: Dict[str, Any] = {}
        self._current_nodes: List[str] = []

    @workflow.run
    async def run(self, params: GraphExecutionParams) -> dict:
        graph = GraphDefinition.model_validate(params.graph_definition)
        predecessors = graph.get_predecessors()
        merge = MergeApplicator(GraphState)

        state = GraphState.deserialize(params.state)
        executed: Set[str] = set()
        active: Set[str] = {graph.entry}
        iteration = 0
        max_iterations = 100

        while active and iteration < max_iterations:
            iteration += 1
            self._current_nodes = sorted(active)

            # ── Execute ──────────────────────────────────────────
            results = await self._execute_nodes(active, state)
            state = merge.apply(state, results)

            self._state = state.serialize()
            executed.update(active)

            # ── Route to next nodes ──────────────────────────────
            candidates: Set[str] = set()
            for uid in active:
                candidates.update(
                    await self._resolve_successors(uid, state, graph)
                )

            # Activate nodes whose ALL predecessors are done.
            # No "uid not in executed" guard — nodes CAN re-execute
            # in cycles (a → b → a → b → final). The iteration
            # limit prevents infinite loops.
            active = {
                uid for uid in candidates
                if all(dep in executed for dep in predecessors.get(uid, set()))
            }

        self._current_nodes = []
        return state.serialize()

    # ------------------------------------------------------------------ #
    #  Queries (streaming / observability)
    # ------------------------------------------------------------------ #

    @workflow.query
    def get_state(self) -> dict:
        return self._state

    @workflow.query
    def get_current_nodes(self) -> List[str]:
        return self._current_nodes

    # ------------------------------------------------------------------ #
    #  Node execution
    # ------------------------------------------------------------------ #

    async def _execute_nodes(
            self,
            uids: Set[str],
            state: GraphState,
    ) -> List[GraphState]:
        """Execute node(s) — sequential if one, parallel if many."""
        if len(uids) == 1:
            uid = next(iter(uids))
            result = await self._execute_node(uid, state)
            return [result]
        return await self._execute_nodes_parallel(uids, state)

    async def _execute_node(self, uid: str, state: GraphState) -> GraphState:
        params = ExecuteNodeParams(
            node_uid=uid,
            state=state.serialize(),
        )
        result_dict = await workflow.execute_activity(
            "execute_graph_node",
            params,
            start_to_close_timeout=_NODE_TIMEOUT,
            heartbeat_timeout=_NODE_HEARTBEAT,
            retry_policy=_NODE_RETRY,
        )
        return GraphState.deserialize(result_dict)

    async def _execute_nodes_parallel(
            self,
            uids: Set[str],
            state: GraphState,
    ) -> List[GraphState]:
        tasks = [
            self._execute_node(uid, state)
            for uid in sorted(uids)
        ]
        return list(await asyncio.gather(*tasks))

    # ------------------------------------------------------------------ #
    #  Routing
    # ------------------------------------------------------------------ #

    async def _resolve_successors(
            self,
            uid: str,
            state: GraphState,
            graph: GraphDefinition,
    ) -> Set[str]:
        successors: Set[str] = set()

        # Conditional edge → evaluate, pick branch
        if uid in graph.conditional_edges:
            cond = graph.conditional_edges[uid]
            outcome = await self._evaluate_condition(state, cond.condition_rid)

            # Condition can return:
            #   str   → single target ("agent_a")
            #   list  → multiple targets (Temporal deserializes tuples as lists)
            if isinstance(outcome, str):
                chosen = cond.branches.get(outcome)
                if chosen:
                    successors.add(chosen)
            elif isinstance(outcome, (list, tuple)):
                for target in outcome:
                    chosen = cond.branches.get(target)
                    if chosen:
                        successors.add(chosen)

        # Unconditional edges → all targets
        if uid in graph.edges:
            successors.update(graph.edges[uid])

        return successors

    async def _evaluate_condition(self, state: GraphState, condition_rid: str) -> str:
        params = EvaluateConditionParams(
            condition_rid=condition_rid,
            state=state.serialize(),
        )
        return await workflow.execute_activity(
            "evaluate_condition",
            params,
            start_to_close_timeout=_CONDITION_TIMEOUT,
            retry_policy=_CONDITION_RETRY,
        )
