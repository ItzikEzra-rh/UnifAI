"""
Temporal graph builder.

Extracts topology, mini-blueprints, and step contexts from RTGraphPlan.
The plan PROVIDES everything — no blueprint_id, no external lookups.
"""
from typing import Any, Callable, Dict, List, Optional, Type

from engine.builder.base_graph_builder import BaseGraphBuilder
from engine.executor.temporal_executor import TemporalGraphExecutor
from engine.models import GraphDefinition, NodeDef, ConditionalEdgeDef
from graph.rt_graph_plan import RTGraphPlan
from graph.state.graph_state import GraphState


class TemporalGraphBuilder(BaseGraphBuilder):
    """
    Builds a GraphDefinition with enriched NodeDefs from the plan.

    Each NodeDef carries:
      • node_blueprint — mini BlueprintSpec to rebuild this node remotely
      • step_context — serialized StepContext from the full graph

    The plan provides ALL of this. No blueprint_id needed.
    """

    def __init__(self, state_cls: Type[GraphState]) -> None:
        self._state_cls = state_cls
        self._nodes: Dict[str, NodeDef] = {}
        self._edges: Dict[str, List[str]] = {}
        self._conditional_edges: Dict[str, ConditionalEdgeDef] = {}
        self._entry: Optional[str] = None
        self._exit: Optional[str] = None

    # ------------------------------------------------------------------ #
    #  BaseGraphBuilder abstract methods
    # ------------------------------------------------------------------ #

    def add_node(self, uid: str, func: Callable[[Dict[str, Any]], Dict[str, Any]]) -> None:
        if uid not in self._nodes:
            self._nodes[uid] = NodeDef(uid=uid, rid=uid)

    def add_edge(self, from_node: str, to_node: str) -> None:
        self._edges.setdefault(from_node, []).append(to_node)

    def add_conditional_edge(
            self,
            from_node: str,
            condition: Callable[[Dict[str, Any]], Any],
            branches: Dict[Any, str],
    ) -> None:
        self._conditional_edges[from_node] = ConditionalEdgeDef(
            condition_rid=from_node,
            branches=branches,
        )

    def set_entry(self, uid: str) -> None:
        self._entry = uid

    def set_exit(self, uid: str) -> None:
        self._exit = uid

    def build_executor(self) -> TemporalGraphExecutor:
        graph_def = GraphDefinition(
            nodes=self._nodes,
            edges=self._edges,
            conditional_edges=self._conditional_edges,
            entry=self._entry or "",
            exit_node=self._exit or "",
        )
        return TemporalGraphExecutor(graph_def)

    # ------------------------------------------------------------------ #
    #  Override: extracts deployment info from the plan
    # ------------------------------------------------------------------ #

    def compile_from_plan(self, plan: RTGraphPlan) -> TemporalGraphExecutor:
        # Topology + deployment info for each node
        for step in plan.steps:
            self._nodes[step.uid] = NodeDef(
                uid=step.uid,
                rid=step.rid,
                node_blueprint=plan.get_node_blueprint(step.uid),
                step_context=plan.get_node_context(step.uid),
            )

        # Edges
        for step in plan.steps:
            for dep in step.after:
                self._edges.setdefault(dep, []).append(step.uid)

            # Conditional edges with condition blueprint + context
            if step.exit_condition and step.branches:
                self._conditional_edges[step.uid] = ConditionalEdgeDef(
                    condition_rid=step.condition.rid,
                    condition_blueprint=plan.get_condition_blueprint(step.condition.rid),
                    step_context=plan.get_node_context(step.uid),
                    branches=step.branches,
                )

        roots = plan.get_roots()
        leaves = plan.get_leaves()
        if not roots:
            raise ValueError("Plan has no root steps.")
        if not leaves:
            raise ValueError("Plan has no leaf steps.")

        self._entry = roots[0].uid
        self._exit = leaves[0].uid

        return self.build_executor()
