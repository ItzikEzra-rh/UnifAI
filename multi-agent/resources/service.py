from .registry import ResourcesRegistry
from catalog.element_registry import ElementRegistry
from .models import ResourceDoc
from core.enums import ResourceCategory
from pydantic import BaseModel


class ResourcesService:
    """
    Public façade. Performs schema validation via ElementRegistry
    and delegates storage to ResourcesRegistry.
    """

    def __init__(
            self,
            resource_registry: ResourcesRegistry,
            element_registry: ElementRegistry,
    ):
        self._store = resource_registry
        self._schema = element_registry

    # ---------- CRUD ----------
    def create(
            self, *, user_id: str, category: str, type: str, name: str, config: dict
    ) -> ResourceDoc:
        model_cls = self._schema.get_schema(ResourceCategory(category), type)
        cfg_model = model_cls(**config)  # raises ValidationError
        doc = ResourceDoc(
            user_id=user_id,
            category=category,
            type=type,
            name=name,
            config=cfg_model.model_dump(mode="json"),
        )
        return self._store.create(doc)

    def delete(self, rid: str) -> None:
        self._store.delete(rid)

    # ---------- resolve ----------
    def resolve(self, rid: str) -> BaseModel:
        """Return the config as a *Pydantic model instance*."""
        doc = self._store.get(rid)
        model_cls = self._schema.get_schema(
            ResourceCategory(doc.category), doc.type
        )
        return model_cls(**doc.config)

    def get_dict(self, rid: str) -> dict:
        """Raw JSON for UI."""
        return self._store.raw_config(rid)
