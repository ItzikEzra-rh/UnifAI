"""Template models package."""

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

__all__ = [
    # Template core models
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
]
