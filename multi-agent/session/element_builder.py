from registry.element_registry import ElementRegistry
from session.session_registry import SessionRegistry
from schemas.blueprint.blueprint import BlueprintSpec, LLMDef, ToolDef, RetrieverDef, AgentDef


class SessionElementBuilder:
    """
    Builds all session-specific element instances (LLMs, Tools, Retrievers, Agents)
    from a validated BlueprintSpec into a SessionRegistry.
    """

    def __init__(self, element_registry: ElementRegistry) -> None:
        self._elements = element_registry

    def build(self, spec: BlueprintSpec) -> SessionRegistry:
        session = SessionRegistry()
        self._build_llms(session, spec.llms)
        self._build_tools(session, spec.tools)
        self._build_retrievers(session, spec.retrievers)
        self._build_agents(session, spec.agents)
        return session

    def _build_llms(self, session: SessionRegistry, defs: list[LLMDef]) -> None:
        for d in defs:
            factory = self._elements.get_factory_or_class(d.name)
            schema = self._elements.get_schema(d.name)
            cfg = schema(**d.dict()) if schema else {}
            inst = factory().create(cfg)
            session.register_llm(d.name, inst)

    def _build_tools(self, session: SessionRegistry, defs: list[ToolDef]) -> None:
        for d in defs:
            factory = self._elements.get_factory_or_class(d.name)
            schema = self._elements.get_schema(d.name)
            cfg = schema(**d.dict()) if schema else {}
            inst = factory().create(cfg)
            session.register_tool(d.name, inst)

    def _build_retrievers(self, session: SessionRegistry, defs: list[RetrieverDef]) -> None:
        for d in defs:
            factory = self._elements.get_factory_or_class(d.name)
            schema = self._elements.get_schema(d.name)
            cfg = schema(**d.dict()) if schema else {}
            inst = factory().create(cfg)
            session.register_retriever(d.name, inst)

    def _build_agents(self, session: SessionRegistry, defs: list[AgentDef]) -> None:
        for d in defs:
            factory = self._elements.get_factory_or_class(d.name)
            schema = self._elements.get_schema(d.name)
            cfg = schema(**d.dict()) if schema else {}
            inst = factory().create(cfg, session)
            session.register_agent(d.name, inst)
