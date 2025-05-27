from typing import Callable, Any, List, TypeVar
from pydantic import BaseModel, ValidationError

from registry.element_registry import ElementRegistry
from session.session_registry import SessionRegistry
from schemas.blueprint.blueprint import BlueprintSpec
from plugins.base_factory import BaseFactory
from plugins.exceptions import PluginConfigurationError
from schemas.blueprint.typing import BlueprintElementDef

T = TypeVar("T", bound=BlueprintElementDef)


class SessionElementBuilder:
    """
    Builds session-scoped instances (LLMs, Tools, Retrievers, etc.)
    by looking up factories & schemas in ElementRegistry under (category, type).
    """

    def __init__(self, element_registry: ElementRegistry) -> None:
        self._elements = element_registry

    def build(self, spec: BlueprintSpec) -> SessionRegistry:
        session = SessionRegistry()

        # for each category in your blueprint, call the generic builder
        self._build_category("llm", spec.llms, session.register_llm)
        self._build_category("tool", spec.tools, session.register_tool)
        self._build_category("retriever", spec.retrievers, session.register_retriever)
        self._build_category("condition", spec.conditions, session.register_condition)

        return session

    def _build_category(
            self,
            category: str,
            definitions: List[T],
            register_fn: Callable[[str, Any], None]
    ) -> None:
        """
        Generic builder for any component category.
        :param category:     one of "llm", "tool", "retriever", "node", etc.
        :param definitions:  list of ElementDefinition (with .name, .type, .dict())
        :param register_fn:  e.g. session.register_llm(name, instance)
        """
        for d in definitions:
            # 1) Lookup factory & schema by category + type
            try:
                factory_cls = self._elements.get_factory(category, d.type)
                schema_cls = self._elements.get_schema(category, d.type)
            except KeyError as e:
                raise PluginConfigurationError(
                    f"No plugin for {category!r} with type={d.type!r}",
                    getattr(d, "dict", lambda **_: {})(exclude_unset=True)
                ) from e

            # 2) Validate & merge via Pydantic if we have a schema
            raw = d.dict(exclude_unset=True)
            try:
                cfg = schema_cls(**raw) if schema_cls else raw
            except ValidationError as ve:
                raise PluginConfigurationError(
                    f"Config validation failed for {category}/{d.type}: {ve}",
                    raw
                ) from ve

            # 3) Instantiate via the factory
            factory: BaseFactory = factory_cls()
            if not factory.accepts(cfg):
                raise PluginConfigurationError(
                    f"{factory_cls.__name__} rejects config for {category}/{d.type}",
                    cfg.dict()  # type: ignore
                )

            try:
                instance = factory.create(cfg)
            except Exception as e:
                raise PluginConfigurationError(
                    f"Factory.create() failed for {category}/{d.type}: {e}",
                    cfg.dict()  # type: ignore
                ) from e

            # 4) Register the instance under the user‐chosen name
            register_fn(d.name, instance)
