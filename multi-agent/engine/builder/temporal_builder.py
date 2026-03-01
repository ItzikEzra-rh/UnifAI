"""
Temporal-native graph builder.

Captures both topology (serializable) and callables (in-memory) from
RTGraphPlan.  Produces a TemporalGraphExecutor that can run the graph
through Temporal with full durability, retry, and parallel fan-out.

Mirrors LangGraphBuilder: LG stores callables in a StateGraph;
we store them in a GraphNodeActivities instance.
"""
from typing import Any, Callable, Dict, List, Optional, Type

from engine.builder.base_graph_builder import BaseGraphBuilder
from engine.executor.temporal_executor import TemporalGraphExecutor
from engine.models import GraphDefinition, NodeDef, ConditionalEdgeDef
from graph.rt_graph_plan import RTGraphPlan
from graph.state.graph_state import GraphState
from temporal.graph_node_activities import GraphNodeActivities


class TemporalGraphBuilder(BaseGraphBuilder):
    """
    Concrete GraphBuilder that targets Temporal as the execution engine.

    compile_from_plan() captures TWO things from RTGraphPlan:
      1. Topology → GraphDefinition (serializable, sent to workflow)
      2. Callables → GraphNodeActivities (in-memory, registered on worker)
    """

    def __init__(self, state_cls: Type[GraphState]) -> None:
        self._state_cls = state_cls
        self._nodes: Dict[str, NodeDef] = {}
        self._node_funcs: Dict[str, Callable] = {}
        self._condition_funcs: Dict[str, Callable] = {}
        self._edges: Dict[str, List[str]] = {}
        self._conditional_edges: Dict[str, ConditionalEdgeDef] = {}
        self._entry: Optional[str] = None
        self._exit: Optional[str] = None

    # ------------------------------------------------------------------ #
    #  BaseGraphBuilder abstract methods (for direct API compatibility)
    # ------------------------------------------------------------------ #

    def add_node(self, uid: str, func: Callable[[Dict[str, Any]], Dict[str, Any]]) -> None:
        self._node_funcs[uid] = func
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
        self._condition_funcs[from_node] = condition
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
        activities = GraphNodeActivities(
            node_funcs=self._node_funcs,
            condition_funcs=self._condition_funcs,
        )
        return TemporalGraphExecutor(graph_def, activities)

    # ------------------------------------------------------------------ #
    #  Override: richer path that captures rids from the plan
    # ------------------------------------------------------------------ #

    def compile_from_plan(self, plan: RTGraphPlan) -> TemporalGraphExecutor:
        """
        Build from RTGraphPlan, capturing both topology and live callables.

        This is the primary path. The RTGraphPlan already has nodes with
        LLM, tools, and StepContext fully bound — we just capture them.
        """
        for step in plan.steps:
            self._nodes[step.uid] = NodeDef(uid=step.uid, rid=step.rid)
            self._node_funcs[step.uid] = step.func

        for step in plan.steps:
            for dep in step.after:
                self._edges.setdefault(dep, []).append(step.uid)

            if step.exit_condition and step.branches:
                self._condition_funcs[step.condition.rid] = step.exit_condition
                self._conditional_edges[step.uid] = ConditionalEdgeDef(
                    condition_rid=step.condition.rid,
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
