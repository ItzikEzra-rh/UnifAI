"""
Template System Module

Provides public blueprint templates with placeholder support.
Allows users to instantiate templates by filling in missing fields,
then materializes resources and blueprints to their account.

Architecture:
- models/: Template data models (Template, PlaceholderMeta)
- repository/: Template persistence
- schema/: Placeholder analysis and dynamic schema generation
- instantiation/: Merge user input into BlueprintDraft
- service.py: Public facade (TemplateService)

Key insight: Templates store valid BlueprintDrafts. Placeholder fields
contain default values that pass validation. The PlaceholderMeta just
points to which fields should be replaced with user input.

Usage:
    from templates import TemplateService
    
    # Get input schema for a template
    schema = template_service.get_input_schema(template_id)
    
    # Instantiate with user input
    blueprint = template_service.instantiate(template_id, user_input)
    
    # Or materialize to user's account
    result = template_service.materialize(
        template_id=template_id,
        user_id=user_id,
        user_input=user_input,
    )
"""

from templates.service import TemplateService
from templates.models.template import (
    Template,
    PlaceholderMeta,
    PlaceholderPointer,
    ResourcePlaceholders,
    CategoryPlaceholders,
    TemplateMetadata,
)
from templates.models.input_schema import (
    ResourceInputSchema,
    CategoryInputSchema,
    TemplateInputSchema,
    FieldDefinition,
)
from templates.instantiation import (
    InstantiationResult,
    MaterializationResult,
    MaterializationError,
)

__all__ = [
    # Main service
    "TemplateService",
    
    # Template models
    "Template",
    "PlaceholderMeta",
    "PlaceholderPointer",
    "ResourcePlaceholders",
    "CategoryPlaceholders",
    "TemplateMetadata",
    
    # Input schema models
    "ResourceInputSchema",
    "CategoryInputSchema",
    "TemplateInputSchema",
    "FieldDefinition",
    
    # Instantiation result models
    "InstantiationResult",
    "MaterializationResult",
    "MaterializationError",
]
