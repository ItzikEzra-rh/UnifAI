"""
Template models for public blueprint templates.

Templates store valid BlueprintDrafts with placeholder metadata
indicating which fields require user input before instantiation.

Key insight: The draft is always valid! Placeholder fields contain
default/dummy values (e.g., "PLACEHOLDER_API_KEY") that pass validation.
The PlaceholderMeta just points to which fields need user input.
"""
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, Extra

from core.enums import ResourceCategory
from blueprints.models.blueprint import BlueprintDraft


class PlaceholderPointer(BaseModel):
    """
    Points to a specific field that requires user input.
    
    Minimal structure - just identifies the field location.
    Type information and validation rules are extracted from
    the element's config_schema at runtime via PlaceholderAnalyzer.
    """
    field_path: str = Field(
        ...,
        description="Dot-notation path to the placeholder field (e.g., 'api_key', 'config.model_name')"
    )
    required: bool = Field(
        default=True,
        description="Whether this field is required for instantiation"
    )
    label: Optional[str] = Field(
        default=None,
        description="Human-readable label for the field (defaults to field name)"
    )
    hint: Optional[str] = Field(
        default=None,
        description="Additional hint text for the user"
    )

    class Config:
        extra = Extra.forbid


class ResourcePlaceholders(BaseModel):
    """
    Placeholder metadata for a single resource.
    
    Links resource ID to its placeholder fields.
    """
    rid: str = Field(..., description="Resource ID within the template")
    placeholders: List[PlaceholderPointer] = Field(
        default_factory=list,
        description="List of placeholder fields for this resource"
    )

    class Config:
        extra = Extra.forbid


class CategoryPlaceholders(BaseModel):
    """
    Placeholder metadata grouped by category.
    """
    category: ResourceCategory
    resources: List[ResourcePlaceholders] = Field(default_factory=list)

    class Config:
        extra = Extra.forbid


class PlaceholderMeta(BaseModel):
    """
    Complete placeholder metadata for a template.
    
    Organized by category > resource > field for easy traversal.
    """
    categories: List[CategoryPlaceholders] = Field(default_factory=list)

    class Config:
        extra = Extra.forbid

    def get_category(self, category: ResourceCategory) -> Optional[CategoryPlaceholders]:
        """Get placeholders for a specific category."""
        for cat in self.categories:
            if cat.category == category:
                return cat
        return None

    def get_resource(self, category: ResourceCategory, rid: str) -> Optional[ResourcePlaceholders]:
        """Get placeholders for a specific resource."""
        cat = self.get_category(category)
        if cat is None:
            return None
        for res in cat.resources:
            if res.rid == rid:
                return res
        return None

    def iter_all_placeholders(self):
        """
        Iterate over all placeholders.
        
        Yields (category, rid, placeholder) tuples.
        """
        for cat in self.categories:
            for res in cat.resources:
                for placeholder in res.placeholders:
                    yield cat.category, res.rid, placeholder

    def placeholder_count(self) -> int:
        """Return total count of placeholder fields."""
        return sum(1 for _ in self.iter_all_placeholders())


class TemplateMetadata(BaseModel):
    """
    Template metadata for catalog and discovery.
    """
    author: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    version: str = "1.0.0"
    is_public: bool = True
    preview_image_url: Optional[str] = None
    category: Optional[str] = Field(
        default=None,
        description="Template category for catalog organization (e.g., 'Chat', 'RAG', 'Agents')"
    )
    output_capabilities: List[str] = Field(
        default_factory=list,
        description="List of output capabilities (e.g., 'streaming', 'json', 'markdown')"
    )

    class Config:
        extra = Extra.forbid


class Template(BaseModel):
    """
    A public blueprint template with placeholder support.
    
    Combines:
    - BlueprintDraft: A valid blueprint (placeholder fields have default values)
    - PlaceholderMeta: Metadata about which fields need user input
    - TemplateMetadata: Catalog metadata (author, tags, etc.)
    
    The draft is always valid! Placeholder fields contain default/dummy values
    that pass Pydantic validation. The PlaceholderMeta just points to which
    fields should be replaced with user input.
    """
    template_id: str = Field(..., description="Unique template identifier")
    draft: BlueprintDraft = Field(..., description="The template blueprint (valid, with placeholder defaults)")
    placeholders: PlaceholderMeta = Field(
        default_factory=PlaceholderMeta,
        description="Metadata about placeholder fields"
    )
    metadata: TemplateMetadata = Field(
        default_factory=TemplateMetadata,
        description="Template catalog metadata"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        extra = Extra.forbid

    @property
    def name(self) -> str:
        """Template name (from draft)."""
        return self.draft.name

    @property
    def description(self) -> str:
        """Template description (from draft)."""
        return self.draft.description

    def has_placeholders(self) -> bool:
        """Check if template has any placeholders."""
        return self.placeholders.placeholder_count() > 0
