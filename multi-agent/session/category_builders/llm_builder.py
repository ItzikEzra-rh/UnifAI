from typing import Any, Iterable
from .category_builder import CategoryBuilder
from core.enums import ResourceCategory


class LLMBuilder(CategoryBuilder):
    category = ResourceCategory.LLM

    def _iter_specs(self, blueprint) -> Iterable[Any]:
        return blueprint.llms


