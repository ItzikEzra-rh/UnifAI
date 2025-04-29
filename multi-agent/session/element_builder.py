from typing import TypeVar, Callable
from registry.element_registry import ElementRegistry
from session.session_registry import SessionRegistry
from schemas.blueprint.blueprint import BlueprintSpec, LLMDef, ToolDef, RetrieverDef, AgentDef

T = TypeVar('T')


class SessionElementBuilder:
    """
    Builds all session-specific element instances (LLMs, Tools, Retrievers, Agents)
    from a validated BlueprintSpec into a SessionRegistry.
    """

    def __init__(self, element_registry: ElementRegistry) -> None:
        self._elements = element_registry

    def build(self, spec: BlueprintSpec) -> SessionRegistry:
        session = SessionRegistry()

        self._build_elements(defs=spec.llms, register_fn=session.register_llm)

        self._build_elements(defs=spec.tools, register_fn=session.register_tool
                             )

        self._build_elements(defs=spec.retrievers, register_fn=session.register_retriever
                             )

        self._build_elements(defs=spec.agents, register_fn=session.register_agent)

        return session

    def _build_elements(
            self,
            defs: list[T],
            register_fn: Callable[[str, object], None],
    ) -> None:
        for definition in defs:
            factory_cls = self._elements.get_factory_or_class(definition.name)
            factory = factory_cls()
            schema = self._elements.get_schema(definition.name)
            config = schema(**definition.dict()) if schema else {}
            if not factory.accepts(config):
                raise ValueError(f"Factory {factory} does not accept config for '{definition.name}'")

            instance = factory.create(config)

            register_fn(definition.name, instance)
