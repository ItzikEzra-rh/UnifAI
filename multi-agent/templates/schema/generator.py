"""
Schema generator and input validator for templates.

Since PlaceholderAnalyzer now creates real Pydantic models directly,
this module provides validation utilities on top of those models.
"""
from typing import Dict, Any, Type, List
from pydantic import BaseModel

from templates.schema.analyzer import PlaceholderAnalyzer
from templates.models.template import Template


class SchemaGenerator:
    """
    Generates Pydantic input models for templates.
    
    Wraps PlaceholderAnalyzer to provide a clean interface.
    """

    def __init__(self, analyzer: PlaceholderAnalyzer):
        self._analyzer = analyzer

    def generate(self, template: Template) -> Type[BaseModel]:
        """
        Generate a Pydantic model for template input.
        
        Returns a real Pydantic model that validates user input.
        """
        return self._analyzer.create_input_model(template)

    def get_json_schema(self, template: Template) -> Dict[str, Any]:
        """
        Get JSON schema for template input.
        
        Returns the complete JSON schema including $defs.
        """
        return self._analyzer.get_json_schema(template)


class InputValidator:
    """
    Validates user input against template schema.
    
    Uses the generated Pydantic model for validation.
    """

    def __init__(self, analyzer: PlaceholderAnalyzer):
        self._analyzer = analyzer
        self._cached_models: Dict[str, Type[BaseModel]] = {}

    def validate(
        self,
        template: Template,
        user_input: Dict[str, Any],
    ) -> BaseModel:
        """
        Validate user input against the template schema.
        
        Returns validated Pydantic model instance.
        Raises ValidationError if input doesn't match schema.
        """
        model = self._get_or_create_model(template)
        return model(**user_input)

    def is_valid(
        self,
        template: Template,
        user_input: Dict[str, Any],
    ) -> bool:
        """Check if user input is valid without raising exceptions."""
        try:
            self.validate(template, user_input)
            return True
        except Exception:
            return False

    def get_validation_errors(
        self,
        template: Template,
        user_input: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Get detailed validation errors.
        
        Returns list of error dictionaries with field paths and messages.
        """
        try:
            self.validate(template, user_input)
            return []
        except Exception as e:
            if hasattr(e, "errors"):
                return [
                    {
                        "field": ".".join(str(loc) for loc in err.get("loc", [])),
                        "message": err.get("msg", "Unknown error"),
                        "type": err.get("type", "unknown"),
                    }
                    for err in e.errors()
                ]
            return [{"field": "", "message": str(e), "type": "unknown"}]

    def _get_or_create_model(self, template: Template) -> Type[BaseModel]:
        """Get cached model or create new one."""
        cache_key = template.template_id
        
        if cache_key not in self._cached_models:
            self._cached_models[cache_key] = self._analyzer.create_input_model(template)
        
        return self._cached_models[cache_key]

    def clear_cache(self):
        """Clear cached models."""
        self._cached_models.clear()
