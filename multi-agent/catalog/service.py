from typing import List, Dict, Any
from pydantic import BaseModel
from core.enums import ResourceCategory
from catalog.element_registry import ElementRegistry


class CatalogService:
    """
    Thin, stateless façade – converts registry information into
    JSON-serialisable shapes the UI (or REST) likes.
    """

    def __init__(self, registry: ElementRegistry):
        self.reg = registry

    # ------------------ browse ---------------------------------------
    def list_categories(self) -> List[str]:
        return [c.value for c in self.reg.list_categories()]

    def list_types(self, category: str) -> List[str]:
        cat_enum = ResourceCategory(category)
        return self.reg.list_types(cat_enum)

    def get_schema_json(self, category: str, type_key: str) -> Dict[str, Any]:
        cat_enum = ResourceCategory(category)
        schema_cls: type[BaseModel] = self.reg.get_schema(cat_enum, type_key)
        return schema_cls.model_json_schema()

    def get_description(self, category: str, type_key: str) -> str:
        cat_enum = ResourceCategory(category)
        return self.reg.get(cat_enum, type_key).description
