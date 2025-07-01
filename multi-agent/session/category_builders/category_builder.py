from abc import ABC, abstractmethod
from typing import Any, ClassVar, Iterable
from plugins.exceptions import PluginConfigurationError
from pydantic import ValidationError
from core.enums import ResourceCategory
from core.contracts import SessionRegistry
from blueprints.models.blueprint import BlueprintSpec, ResourceSpec


class CategoryBuilder(ABC):
    """SRP: one concrete subclass per resource category."""

    # must be overridden
    category: ClassVar[ResourceCategory]
    depends_on: ClassVar[tuple[ResourceCategory, ...]] = ()

    def __init__(self, registry_elements) -> None:
        self._registry_elements = registry_elements

    def build(self, blueprint: BlueprintSpec, registry: SessionRegistry) -> None:
        for resource in self._iter_specs(blueprint):
            inst = self._create_instance(resource.config, registry)
            self._register(registry, resource.rid.ref, inst)

    # -------- protected helpers ----------------------------------------

    @abstractmethod
    def _iter_specs(self, blueprint: BlueprintSpec) -> Iterable[ResourceSpec]:
        ...

    def _register(self, registry, name: str, inst: Any):
        registry.register(self.category, name, inst)

    # ––– shared factory construction with error handling ––––––––––––––
    def _create_instance(self, cfg, session_registry: SessionRegistry) -> Any:
        """Lookup factory, validate schema, create instance with extras."""
        try:
            factory_cls = self._registry_elements.get_factory(self.category, cfg.type)
            schema_cls = self._registry_elements.get_schema(self.category, cfg.type)
        except KeyError as e:
            raise PluginConfigurationError(
                f"No plugin for {self.category!r} type={cfg.type!r}", cfg.dict()
            ) from e

        # schema validation / merge
        raw = cfg.dict(exclude_unset=True)
        try:
            validated = schema_cls(**raw) if schema_cls else raw
        except ValidationError as ve:
            raise PluginConfigurationError(
                f"Config validation failed for {self.category}/{cfg.type}: {ve}", raw
            ) from ve

        factory = factory_cls()
        if not factory.accepts(validated):
            raise PluginConfigurationError(
                f"{factory_cls.__name__} rejects config", validated
            )

        try:
            return factory.create(validated, **self._extra_kwargs(cfg, session_registry))
        except Exception as e:
            raise PluginConfigurationError(
                f"{factory_cls.__name__}.create() failed: {e}", validated
            ) from e

    # subclasses may override
    def _extra_kwargs(self, cfg, session_registry: SessionRegistry) -> dict[str, Any]:
        return {}
