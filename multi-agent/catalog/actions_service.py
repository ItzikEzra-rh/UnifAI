from typing import List, Dict, Any, Optional, Type
from elements.common.actions import BaseAction
from elements.common.base_element_spec import BaseElementSpec
from .element_registry import ElementRegistry
from core.enums import ResourceCategory


class ElementActionsService:
    """
    Catalog service for element actions and actionable capabilities.
    
    Lives in catalog layer as it provides discovery and access to element actions,
    extending the catalog functionality to include actionable operations.
    
    This service catalogs and provides access to administrative/diagnostic operations
    that can be performed on elements (validate, discover, inspect, etc.).
    
    Responsibilities:
    - Discover actions from element specs by category and type
    - Execute element actions with proper sync handling
    - Provide metadata about available element actions
    - Validate action inputs
    """
    
    def __init__(self, element_registry: ElementRegistry):
        self._element_registry = element_registry
    
    def get_element_actions(self, category: str, element_type: str) -> List[BaseAction]:
        """Get all actions for an element by category and type"""
        spec = self._get_spec(category, element_type)
        if spec and hasattr(spec, 'actions') and spec.actions:
            return [action_cls() for action_cls in spec.actions]
        return []
    
    def get_element_action(self, category: str, element_type: str, action_name: str) -> Optional[BaseAction]:
        """Get specific action for an element by category and type"""
        spec = self._get_spec(category, element_type)
        if spec and hasattr(spec, 'actions') and spec.actions:
            for action_cls in spec.actions:
                action = action_cls()
                if action.name == action_name:
                    return action
        return None
    
    def get_element_actions_metadata(self, category: str, element_type: str) -> List[Dict[str, Any]]:
        """Get metadata for all actions of an element by category and type"""
        spec = self._get_spec(category, element_type)
        if spec and hasattr(spec, 'actions') and spec.actions:
            return [action_cls.get_metadata() for action_cls in spec.actions]
        return []
    
    def get_all_elements_with_actions(self) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
        """Get all elements that have actions and their metadata, organized by category"""
        elements_with_actions = {}
        
        for category_enum, specs_dict in self._element_registry._specs.items():
            category_name = category_enum.value
            elements_with_actions[category_name] = {}
            
            for element_type, spec_cls in specs_dict.items():
                if hasattr(spec_cls, 'actions') and spec_cls.actions:
                    elements_with_actions[category_name][element_type] = [
                        action_cls.get_metadata() for action_cls in spec_cls.actions
                    ]
        
        # Remove empty categories
        elements_with_actions = {k: v for k, v in elements_with_actions.items() if v}
        
        return elements_with_actions
    
    def execute_action_sync(
        self, 
        category: str,
        element_type: str, 
        action_name: str, 
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute action synchronously"""
        action = self.get_element_action(category, element_type, action_name)
        if not action:
            raise ValueError(f"Action '{action_name}' not found for element '{category}/{element_type}'")
        
        validated_input = action.validate_input(input_data)
        result = action.execute_sync(validated_input)
        return result.model_dump()
    
    def validate_action_input(
        self, 
        category: str,
        element_type: str, 
        action_name: str, 
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate action input without executing"""
        action = self.get_element_action(category, element_type, action_name)
        if not action:
            raise ValueError(f"Action '{action_name}' not found for element '{category}/{element_type}'")
        
        validated_input = action.validate_input(input_data)
        return validated_input.model_dump()
    
    def element_exists(self, category: str, element_type: str) -> bool:
        """Check if an element exists by category and type"""
        try:
            category_enum = ResourceCategory(category)
            return self._element_registry.has_spec(category_enum, element_type)
        except ValueError:
            # Invalid category
            return False
    
    def _get_spec(self, category: str, element_type: str) -> Optional[Type[BaseElementSpec]]:
        """Helper to get spec class using ElementRegistry.get_spec method"""
        try:
            category_enum = ResourceCategory(category)
            return self._element_registry.get_spec(category_enum, element_type)
        except (ValueError, KeyError):
            # Invalid category or spec not found
            return None