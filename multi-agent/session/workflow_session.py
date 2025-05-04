# core/workflow_session.py

from session.session_registry import SessionRegistry
from schemas.blueprint.blueprint import BlueprintSpec
from graph.graph_plan import GraphPlan
from engine.builder.base_graph_builder import BaseGraphBuilder
from engine.executor.interfaces import GraphExecutor
from typing import Any, Dict


class WorkflowSession:
    """
    Holds all runtime state for a single user-run of a blueprint:
      - session_registry: dynamic component instances (LLMs, agents, etc.)
      - blueprint: the validated BlueprintSpec
      - graph_plan: the abstract plan (list of Steps)
      - executable_graph: compiled graph ready to invoke()
      - logger: records every event
      - builder: the graph builder used (for live recompilation)
      - metadata: arbitrary dict (run_id, timestamps, user_id, etc.)
    """

    def __init__(
            self,
            session_registry: SessionRegistry,
            blueprint: BlueprintSpec,
            graph_plan: GraphPlan,
            executable_graph: GraphExecutor,
            builder: BaseGraphBuilder,
            metadata: Dict[str, Any] = None,
    ) -> None:
        self.session_registry = session_registry
        self.blueprint = blueprint
        self.graph_plan = graph_plan
        self.executable_graph = executable_graph
        # self.logger = logger
        self.builder = builder
        self.metadata = metadata or {}

    def recompile(self) -> None:
        """
        Rebuilds the executable_graph from the current graph_plan,
        using the stored builder.
        """
        self.executable_graph = self.builder.compile_from_plan(self.graph_plan)
