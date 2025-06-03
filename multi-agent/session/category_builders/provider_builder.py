from typing import Any, Iterable

from .category_builder import CategoryBuilder
from core.enums import ResourceCategory


class ProviderBuilder(CategoryBuilder):
    category = ResourceCategory.PROVIDER

    def _iter_specs(self, blueprint) -> Iterable[Any]:
        return blueprint.providers
