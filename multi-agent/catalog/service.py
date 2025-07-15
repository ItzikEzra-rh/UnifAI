from typing import List, Dict, Any
from pydantic import BaseModel
from core.enums import ResourceCategory
from catalog.element_registry import ElementRegistry
from catalog.element_definition import ElementDefinition


class CatalogService:
    """
    Enhanced catalog service that works with both new BaseElementSpec instances
    and legacy ElementDefinition objects.
    
    Converts registry information into JSON-serialisable shapes the UI likes.
    """

    def __init__(self, registry: ElementRegistry):
        self.reg = registry

    # ------------------ browse ---------------------------------------
    def list_categories(self) -> List[str]:
        """List all available element categories"""
        return [c.value for c in self.reg.list_categories()]

    def list_types(self, category: str) -> List[str]:
        """List all element types in a category"""
        cat_enum = ResourceCategory(category)
        return self.reg.list_types(cat_enum)

    def get_schema_json(self, category: str, type_key: str) -> Dict[str, Any]:
        """Get JSON schema for an element type (works with both specs and legacy)"""
        cat_enum = ResourceCategory(category)
        return self.reg.get_schema_json(cat_enum, type_key)

    def get_description(self, category: str, type_key: str) -> str:
        """Get description for an element type"""
        cat_enum = ResourceCategory(category)
        
        # Try spec first (new system)
        if self.reg.has_spec(cat_enum, type_key):
            spec = self.reg.get_spec(cat_enum, type_key)
            return spec.description
        
        # Fallback to legacy system
        return self.reg.get(cat_enum, type_key).description

    def get_element_info(self, category: str, type_key: str) -> ElementDefinition:
        """Get complete element information as UI DTO"""
        cat_enum = ResourceCategory(category)
        return self.reg.get_ui_dto(cat_enum, type_key)

    def list_all_elements(self) -> Dict[str, List[ElementDefinition]]:
        """Get all elements organized by category as UI DTOs"""
        result = {}
        for category in self.list_categories():
            cat_enum = ResourceCategory(category)
            elements = []
            for type_key in self.reg.list_types(cat_enum):
                elements.append(self.reg.get_ui_dto(cat_enum, type_key))
            result[category] = elements
        return result

    def debug_registry_state(self) -> Dict[str, Any]:
        """Get debug information about the registry state"""
        return self.reg.debug_info()
