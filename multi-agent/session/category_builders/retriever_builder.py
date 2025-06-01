from .category_builder import CategoryBuilder
from core.enums import ResourceCategory
from typing import Iterable, Any


class RetrieverBuilder(CategoryBuilder):
    category = ResourceCategory.RETRIEVER

    def _iter_specs(self, blueprint) -> Iterable[Any]:
        return blueprint.retrievers
