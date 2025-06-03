from .category_builder import CategoryBuilder
from core.enums import ResourceCategory
from typing import Iterable, Any


class ConditionBuilder(CategoryBuilder):
    category = ResourceCategory.CONDITION

    def _iter_specs(self, blueprint) -> Iterable[Any]:
        return blueprint.conditions
