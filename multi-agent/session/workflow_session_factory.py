from typing import Optional
from blueprints.loader.base_blueprint_loader import BaseBlueprintLoader
from registry.element_registry import ElementRegistry
from .element_builder import SessionElementBuilder
from composers.plan_composer import PlanComposer
# from engine.engine_factory import EngineFactory
from .workflow_session import WorkflowSession


# from logs.in_memory_logger import InMemoryLogger

class WorkflowSessionFactory:
    """
    Orchestrates the creation of a WorkflowSession end-to-end:
      1) Load & validate blueprint via BaseBlueprintLoader
      2) Instantiate atomic elements via ComponentConfigurator
      3) Build GraphPlan via PlanComposer
      4) Compile to ExecutableGraph via EngineFactory
      5) Package into WorkflowSession
    """

    def __init__(
            self,
            element_registry: ElementRegistry,
            blueprint_loader: BaseBlueprintLoader,
            plan_composer,
            engine_factory,
            logger_factory: Optional[callable] = None,
    ):
        self._elements = element_registry
        self._loader = blueprint_loader
        self._session_element_builder = SessionElementBuilder(element_registry=self._elements)
        self._composer = None
        self._engines = engine_factory
        # self._make_logger = logger_factory or (lambda: InMemoryLogger())

    def create(self, blueprint_path: str, engine_name: str = "langgraph", metadata: dict = None):
        # 1) Load & validate blueprint
        spec = self._loader.load(blueprint_path)
        # print(spec)
        # 2) Instantiate session-wide components
        session_registry = self._session_element_builder.build(spec)
        # # 3) Build the abstract plan
        self._composer = PlanComposer(session_registry=session_registry)
        graph_plan = self._composer.compose(spec.plan)
        print(graph_plan.pretty_print())

        # 4) Compile to executable graph
        # builder = self._engines.get_builder(engine_name)
        # executable_graph = builder.build(graph_plan)
        #
        # # 5) Create logger + session
        # logger = self._make_logger()
        # session = WorkflowSession(
        #     session_registry=session_registry,
        #     blueprint=spec,
        #     graph_plan=graph_plan,
        #     executable_graph=executable_graph,
        #     logger=logger,
        #     builder=builder,
        #     metadata=metadata,
        # )
        # return session
