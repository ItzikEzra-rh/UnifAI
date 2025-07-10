from .registry import ResourcesRegistry
from catalog.element_registry import ElementRegistry
from .models import ResourceDoc
from core.enums import ResourceCategory
from core.ref import RefWalker
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
        self.element_registry = element_registry

    # ---------- CRUD ----------
    def create(self, *, user_id, category, type, name, config) -> ResourceDoc:
        # schema validation
        model_cls = self.element_registry.get_schema(ResourceCategory(category), type)
        cfg_model = model_cls(**config)  # Pydantic instance

        # traverse refs on the *model*
        nested_refs = list(RefWalker.external_rids(cfg_model))

        # build the document for storage
        doc = ResourceDoc(
            user_id=user_id,
            category=category,
            type=type,
            name=name,
            cfg_dict=cfg_model.model_dump(mode="json"),
            nested_refs=nested_refs,
        )
        return self._store.create(doc)

    def update(self, rid: str, *, config: dict) -> ResourceDoc:
        # 1. fetch immutable meta
        doc = self._store.get(rid)  # existing ResourceDoc
        model_cls = self.element_registry.get_schema(
            ResourceCategory(doc.category), doc.type)
        cfg_model = model_cls(**config)  # validate

        # 2. recompute nested refs
        nested_refs = list(RefWalker.external_rids(cfg_model))

        # 3. build a *new* ResourceDoc (immutability) or mutate doc
        doc.cfg_dict = cfg_model.model_dump(mode="json")
        doc.nested_refs = nested_refs
        return self._store.update(doc)

    def delete(self, rid: str) -> None:
        self._store.delete(rid)

    # ---------- resolve ----------
    def resolve(self, rid: str) -> BaseModel:
        category, _type = self._store.meta(rid)
        model_cls = self.element_registry.get_schema(ResourceCategory(category), _type)
        return model_cls(**self._store.raw_config(rid))

    def get_dict(self, rid: str) -> dict:
        """Raw JSON for UI."""
        return self._store.raw_config(rid)
