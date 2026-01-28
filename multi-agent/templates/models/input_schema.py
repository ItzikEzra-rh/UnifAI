"""
Input schema models for template instantiation.

These models represent the dynamically generated schema that users
must fill in to instantiate a template.
"""
from typing import List, Dict, Any, Optional, Type
from pydantic import BaseModel, Field, Extra, PrivateAttr

from core.enums import ResourceCategory


class FieldDefinition(BaseModel):
    """
    Field definition for a single input field.
    
    Contains the complete JSON schema for the field, copied directly
    from the element's config_schema via Pydantic's model_json_schema().
    
    This is generic - all types, constraints, and json_schema_extra
    are preserved exactly as defined in the original schema.
    """
    field_path: str = Field(..., description="Dot-notation path to the field")
    field_name: str = Field(..., description="Field name for display")
    required: bool = Field(default=True)
    
    # Complete JSON schema for this field - copied as-is from Pydantic
    schema: Dict[str, Any] = Field(
        default_factory=dict,
        description="Complete JSON schema from Pydantic model_json_schema()"
    )

    class Config:
        extra = Extra.forbid


class ResourceInputSchema(BaseModel):
    """
    Input schema for a single resource.
    
    Contains all fields that need to be filled for this resource,
    plus the $defs from Pydantic for complex types.
    """
    rid: str = Field(..., description="Resource ID within the template")
    resource_name: Optional[str] = Field(default=None, description="Resource display name")
    element_type: str = Field(..., description="Element type (e.g., 'openai_llm')")
    category: ResourceCategory
    fields: List[FieldDefinition] = Field(default_factory=list)
    
    # $defs from Pydantic schema for complex types (LLMRef, etc.)
    defs: Dict[str, Any] = Field(
        default_factory=dict,
        description="$defs from Pydantic for complex type references"
    )

    class Config:
        extra = Extra.forbid


class CategoryInputSchema(BaseModel):
    """
    Input schema grouped by category.
    """
    category: ResourceCategory
    resources: List[ResourceInputSchema] = Field(default_factory=list)

    class Config:
        extra = Extra.forbid


class TemplateInputSchema(BaseModel):
    """
    Complete input schema for a template.
    
    This is what the frontend uses to render the form and
    what gets validated against user input.
    """
    template_id: str
    template_name: str
    categories: List[CategoryInputSchema] = Field(default_factory=list)
    
    # The dynamically generated Pydantic model class (not serialized)
    # Used for validation at runtime (PrivateAttr for Pydantic V2)
    _validation_model: Optional[Type[BaseModel]] = PrivateAttr(default=None)

    class Config:
        extra = Extra.forbid

    def get_category(self, category: ResourceCategory) -> Optional[CategoryInputSchema]:
        """Get schema for a specific category."""
        for cat in self.categories:
            if cat.category == category:
                return cat
        return None

    def get_resource(self, category: ResourceCategory, rid: str) -> Optional[ResourceInputSchema]:
        """Get schema for a specific resource."""
        cat = self.get_category(category)
        if cat is None:
            return None
        for res in cat.resources:
            if res.rid == rid:
                return res
        return None

    def field_count(self) -> int:
        """Return total count of input fields."""
        return sum(
            len(res.fields)
            for cat in self.categories
            for res in cat.resources
        )

    def to_json_schema(self) -> Dict[str, Any]:
        """
        Convert to JSON Schema format for frontend consumption.
        
        Creates a nested schema with $defs for complex types:
        {
            "type": "object",
            "$defs": { ... complex type definitions ... },
            "properties": {
                "llms": {
                    "type": "object",
                    "properties": {
                        "rid_123": {
                            "type": "object",
                            "properties": {
                                "api_key": {"type": "string", ...}
                            }
                        }
                    }
                }
            }
        }
        """
        properties = {}
        required_cats = []
        all_defs: Dict[str, Any] = {}  # Collect all $defs

        for cat in self.categories:
            cat_props = {}
            required_resources = []

            for res in cat.resources:
                res_props = {}
                required_fields = []
                
                # Merge resource's $defs into all_defs
                if res.defs:
                    all_defs.update(res.defs)

                for field in res.fields:
                    field_schema = self._field_to_json_schema(field)
                    res_props[field.field_name] = field_schema
                    if field.required:
                        required_fields.append(field.field_name)

                cat_props[res.rid] = {
                    "type": "object",
                    "properties": res_props,
                    "required": required_fields,
                    "title": res.resource_name or res.rid,
                }
                required_resources.append(res.rid)

            if cat_props:
                properties[cat.category.value] = {
                    "type": "object",
                    "properties": cat_props,
                    "required": required_resources,
                }
                required_cats.append(cat.category.value)

        result = {
            "type": "object",
            "title": f"Input for {self.template_name}",
            "properties": properties,
            "required": required_cats,
        }
        
        # Include $defs if any complex types are referenced
        if all_defs:
            result["$defs"] = all_defs
        
        return result

    def _field_to_json_schema(self, field: FieldDefinition) -> Dict[str, Any]:
        """Return the field's schema as-is from Pydantic."""
        return field.schema
