from typing import TypeVar
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
    """
    Turns BlueprintDraft (may contain $ref) into BlueprintSpec (concrete).
    """

    def __init__(self, resources: ResourcesService):
        self._resources = resources

    # -----------------------------------------------------------------
    def _resolve_cfg(self, cfg: Ref | T) -> T:
        if isinstance(cfg, Ref):
            # ResourcesService returns *model*, not dict
            return self._resources.resolve(cfg.ref)  # type: ignore[return-value]
        return cfg  # already inline/frozen

    def _convert(self, items: list[Resource[T]]) -> list[ResourceSpec[T]]:
        result: list[ResourceSpec[T]] = []
        for entry in items:
            concrete = self._resolve_cfg(entry.config)
            result.append(
                ResourceSpec[type(concrete)](
                    alias=entry.alias,
                    config=concrete
                )
            )
        return result

    # -----------------------------------------------------------------
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
