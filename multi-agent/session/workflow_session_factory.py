from catalog.element_registry import ElementRegistry
from session.element_builder import SessionElementBuilder
from session.session_registry import SessionRegistry
from engine.factory import GraphBuilderFactory
from session.workflow_session import WorkflowSession
from graph.state.graph_state import GraphState
from graph.plan_builder import PlanBuilder
from graph.rt_graph_plan import RTGraphPlan
from core.run_context import RunContext
from core.context import set_current_context
from blueprints.models.blueprint import BlueprintSpec
from .models import SessionMeta


class WorkflowSessionFactory:
    """
    Orchestrates the creation of a WorkflowSession end-to-end.

    Exposes reusable build methods for Temporal workers:
      • build_runtime_plan() — full plan with bound callables
      • build_session_registry() — just the element instances
    """

    def __init__(
            self,
            element_registry: ElementRegistry,
            engine_name: str,
    ):
        self._elements = element_registry
        self._session_builder = SessionElementBuilder(element_registry)
        self._engine_name = engine_name

    def build_runtime_plan(self, blueprint_spec: BlueprintSpec) -> RTGraphPlan:
        """
        Build an RTGraphPlan from a blueprint spec.

        Creates all session components, binds callables, injects StepContext.
        Used by create() and Temporal node activities.
        """
        logical_plan = PlanBuilder(self._elements).build(blueprint_spec)
        session_registry = self._session_builder.build(blueprint_spec)
        return RTGraphPlan(logical_plan, session_registry)

    def build_session_registry(self, blueprint_spec: BlueprintSpec) -> SessionRegistry:
        """
        Build a SessionRegistry from a blueprint spec.

        Creates element instances without building a plan or binding callables.
        Used by Temporal condition activities (conditions don't need a plan).
        """
        return self._session_builder.build(blueprint_spec)

    def create(
            self,
            *,
            user_id: str,
            blueprint_spec: BlueprintSpec,
            blueprint_id: str,
            metadata: SessionMeta = None,
            graph_state: GraphState = GraphState(),
    ) -> WorkflowSession:
        session_meta = metadata if metadata is not None else SessionMeta()

        ctx = RunContext(
            user_id=user_id,
            engine_name=self._engine_name,
            metadata=session_meta.to_dict()
        )
        set_current_context(ctx)

        # 1. Build runtime plan
        rt_graph_plan = self.build_runtime_plan(blueprint_spec)
        rt_graph_plan.pretty_print()

        # 2. Compile to executable graph
        _engine_builder = GraphBuilderFactory(GraphState).create(self._engine_name)
        executable_graph = _engine_builder.compile_from_plan(rt_graph_plan)

        # 3. Wire into WorkflowSession
        session = WorkflowSession(
            session_registry=rt_graph_plan.session_registry,
            blueprint_id=blueprint_id,
            rt_graph_plan=rt_graph_plan,
            executable_graph=executable_graph,
            builder=_engine_builder,
            run_context=ctx,
            metadata=session_meta,
            graph_state=graph_state,
        )

        return session
