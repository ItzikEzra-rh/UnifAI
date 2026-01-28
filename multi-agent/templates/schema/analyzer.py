"""
Placeholder analyzer for extracting fields from element config schemas.

Creates a real Pydantic model by extracting exact field definitions
(type + FieldInfo) from the original configs and merging them.

Single Responsibility: Build input model from placeholder field definitions.
Open/Closed: Extensible via element registry without modifying analyzer.
"""
from typing import List, Dict, Any, Optional, Type, Tuple
from pydantic import BaseModel, Field, create_model
from pydantic.fields import FieldInfo

from catalog.element_registry import ElementRegistry
from core.enums import ResourceCategory
from templates.models.template import Template


class PlaceholderAnalyzer:
    """
    Analyzes templates and creates input Pydantic models.
    
    The key insight: Instead of building custom schema objects,
    we extract the exact (annotation, FieldInfo) tuples from the
    original config schemas and use create_model to build a real
    Pydantic model.
    
    This gives us:
    - Exact same types (LLMRef, SecretStr, etc.)
    - Exact same validation constraints
    - Exact same json_schema_extra metadata
    - Real Pydantic model for validation
    """

    def __init__(self, element_registry: ElementRegistry):
        self._registry = element_registry

    def create_input_model(self, template: Template) -> Type[BaseModel]:
        """
        Create a Pydantic model for template input.
        
        Structure:
        - Root model with category fields
        - Category models with resource fields  
        - Resource models with placeholder fields (extracted from original configs)
        
        Returns a real Pydantic model that can validate user input.
        """
        category_models: Dict[str, Type[BaseModel]] = {}
        
        for cat_placeholder in template.placeholders.categories:
            category = cat_placeholder.category
            resource_models: Dict[str, Type[BaseModel]] = {}
            
            for res_placeholder in cat_placeholder.resources:
                resource_model = self._create_resource_model(
                    template=template,
                    category=category,
                    rid=res_placeholder.rid,
                    field_paths=[p.field_path for p in res_placeholder.placeholders],
                )
                if resource_model:
                    resource_models[res_placeholder.rid] = resource_model
            
            # Create category model from resource models
            if resource_models:
                cat_fields = {
                    rid: (model, Field(..., description=f"Input for {rid}"))
                    for rid, model in resource_models.items()
                }
                category_models[category.value] = create_model(
                    f"{category.value.title()}Input",
                    **cat_fields
                )
        
        # Create root model from category models
        if not category_models:
            return create_model(f"{template.name}Input")
        
        root_fields = {
            cat_name: (model, Field(..., description=f"Input for {cat_name}"))
            for cat_name, model in category_models.items()
        }
        
        return create_model(
            self._sanitize_name(f"{template.name}Input"),
            **root_fields
        )

    def _create_resource_model(
        self,
        template: Template,
        category: ResourceCategory,
        rid: str,
        field_paths: List[str],
    ) -> Optional[Type[BaseModel]]:
        """
        Create a Pydantic model for a resource's placeholder fields.
        
        Extracts the exact (annotation, FieldInfo) from the original
        config schema and builds a new model with just those fields.
        """
        # Find the resource in the template
        resources = getattr(template.draft, category.value, [])
        resource = None
        for r in resources:
            if r.rid.ref == rid:
                resource = r
                break
        
        if resource is None or not resource.type:
            return None
        
        # Get the original config schema
        try:
            schema_cls = self._registry.get_schema(category, resource.type)
        except KeyError:
            return None
        
        # Extract the placeholder fields - exact copy from original
        fields: Dict[str, Tuple[Any, FieldInfo]] = {}
        
        for field_path in field_paths:
            field_name = field_path.split(".")[-1]
            
            if field_name in schema_cls.model_fields:
                field_info = schema_cls.model_fields[field_name]
                # Copy exact type and FieldInfo
                fields[field_name] = (field_info.annotation, field_info)
        
        if not fields:
            return None
        
        return create_model(
            self._sanitize_name(f"{rid}Input"),
            **fields
        )

    def get_json_schema(self, template: Template) -> Dict[str, Any]:
        """
        Get JSON schema for template input.
        
        Creates the input model and returns its JSON schema.
        This includes all $defs for complex types.
        """
        input_model = self.create_input_model(template)
        return input_model.model_json_schema()

    def _sanitize_name(self, name: str) -> str:
        """Sanitize name for use as Python identifier."""
        result = "".join(
            c if c.isalnum() or c == "_" else "_"
            for c in name
        )
        if result and result[0].isdigit():
            result = "_" + result
        return result or "Model"
