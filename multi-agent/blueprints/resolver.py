from typing import Generic, List, TypeVar
from catalog.element_registry import ElementRegistry
from pydantic import BaseModel

from .models.blueprint import (
    Ref,
    Resource,
    ResourceSpec,
    BlueprintDraft,
    BlueprintSpec
)
from resources.service import ResourcesService

T = TypeVar("T", bound=BaseModel)


class BlueprintResolver:
    def __init__(self,
                 res_svc: ResourcesService,
                 catalog: ElementRegistry):
        self.resources = res_svc
        self.catalog = catalog

    def _resolve_cfg(self, cfg: Ref | T) -> T:
        if isinstance(cfg, Ref):
            raw = self.resources.resolve(cfg.ref)
            enum = self.catalog.get_category_from_dict(raw)
            model_cls = self.catalog.get_schema(enum, raw["type"])
            return model_cls(**raw)  # type: ignore[return-value]
        return cfg

    def _convert(self, items: list[Resource[T]]) -> list[ResourceSpec[T]]:
        out: list[ResourceSpec[T]] = []
        for entry in items:
            concrete = self._resolve_cfg(entry.config)
            out.append(ResourceSpec[type(concrete)](
                alias=entry.alias,
                name=getattr(entry, "name", None),
                config=concrete
            ))
        return out

    def resolve(self, draft: BlueprintDraft) -> BlueprintSpec:
        return BlueprintSpec(
            providers=self._convert(draft.providers),
            llms=self._convert(draft.llms),
            retrievers=self._convert(draft.retrievers),
            tools=self._convert(draft.tools),
            nodes=self._convert(draft.nodes),
            conditions=self._convert(draft.conditions),
            plan=draft.plan,
            name=draft.name,
            description=draft.description,
        )
