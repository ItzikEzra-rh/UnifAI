"""
Template instantiator for merging user input into BlueprintDraft.

Single Responsibility: Merge user input into template and produce updated BlueprintDraft.

The template's draft is always a valid BlueprintDraft. Placeholder fields contain
default values that pass validation. This instantiator simply replaces those
defaults with user-provided values.
"""
from typing import Dict, Any, List, Tuple
from copy import deepcopy

from pydantic import BaseModel, Field, Extra

from blueprints.models.blueprint import BlueprintDraft, Resource
from core.enums import ResourceCategory
from templates.models.template import Template, PlaceholderMeta


class MergeError(Exception):
    """Raised when merge fails."""
    
    def __init__(self, message: str, errors: List[Dict[str, Any]] = None):
        super().__init__(message)
        self.errors = errors or []


class InstantiationResult(BaseModel):
    """
    Result of template instantiation.
    
    Contains:
    - blueprint: The merged BlueprintDraft (valid, ready to use)
    - Metadata about what was filled
    """
    blueprint: BlueprintDraft
    template_id: str
    filled_fields: List[str] = Field(default_factory=list)

    class Config:
        extra = Extra.forbid

    @property
    def field_count(self) -> int:
        """Number of fields that were filled."""
        return len(self.filled_fields)


class TemplateInstantiator:
    """
    Merges user input into template draft.
    
    Responsibilities:
    - Deep copy template draft
    - Merge user input values into placeholder positions
    - Return the updated BlueprintDraft
    
    The template draft is already a valid BlueprintDraft - this just
    replaces placeholder default values with actual user input.
    """

    def instantiate(
        self,
        template: Template,
        user_input: Dict[str, Any],
    ) -> BlueprintDraft:
        """
        Instantiate a template with user input.
        
        Args:
            template: The template to instantiate
            user_input: User-provided values structured by category/resource/field
            
        Returns:
            BlueprintDraft with placeholders replaced by user values
            
        Raises:
            MergeError: If merge fails (missing required fields, etc.)
        """
        # Deep copy the draft to avoid modifying the template
        filled_draft = self._deep_copy_draft(template.draft)
        
        # Merge user input into draft
        self._merge_input(filled_draft, template.placeholders, user_input)
        
        return filled_draft

    def instantiate_with_tracking(
        self,
        template: Template,
        user_input: Dict[str, Any],
    ) -> InstantiationResult:
        """
        Instantiate template and return result with tracking info.
        """
        blueprint = self.instantiate(template, user_input)
        
        filled_fields = self._collect_filled_fields(
            template.placeholders,
            user_input,
        )
        
        return InstantiationResult(
            blueprint=blueprint,
            template_id=template.template_id,
            filled_fields=filled_fields,
        )

    def validate_merge(
        self,
        template: Template,
        user_input: Dict[str, Any],
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Validate that merge would succeed.
        
        Returns (is_valid, errors) tuple.
        """
        try:
            self.instantiate(template, user_input)
            return True, []
        except MergeError as e:
            return False, e.errors
        except Exception as e:
            return False, [{"message": str(e)}]

    def _deep_copy_draft(self, draft: BlueprintDraft) -> BlueprintDraft:
        """Create a deep copy of the blueprint draft."""
        # Use model_dump + model_validate for proper Pydantic copy
        return BlueprintDraft.model_validate(draft.model_dump(mode="python"))

    def _merge_input(
        self,
        draft: BlueprintDraft,
        placeholders: PlaceholderMeta,
        user_input: Dict[str, Any],
    ) -> None:
        """
        Merge user input into the draft in-place.
        
        Input structure:
        {
            "llms": {
                "rid_123": {
                    "api_key": "sk-xxx",
                    "model": "gpt-4"
                }
            }
        }
        """
        errors: List[Dict[str, Any]] = []
        
        # Iterate through placeholder metadata
        for cat_placeholders in placeholders.categories:
            category = cat_placeholders.category
            field_name = category.value
            
            # Get user input for this category
            cat_input = user_input.get(category.value, {})
            
            # Get resources in draft
            resources: List[Resource] = getattr(draft, field_name, [])
            
            for res_placeholders in cat_placeholders.resources:
                rid = res_placeholders.rid
                
                # Find the resource in draft
                resource = self._find_resource(resources, rid)
                if resource is None:
                    errors.append({
                        "category": category.value,
                        "rid": rid,
                        "message": f"Resource {rid} not found in draft",
                    })
                    continue
                
                # Get user input for this resource
                res_input = cat_input.get(rid, {})
                
                # Merge each placeholder field
                for placeholder in res_placeholders.placeholders:
                    field_path = placeholder.field_path
                    field_name_only = field_path.split(".")[-1]
                    
                    # Check if user provided value
                    if field_name_only in res_input:
                        value = res_input[field_name_only]
                        self._set_field_value(resource, field_path, value)
                    elif placeholder.required:
                        errors.append({
                            "category": category.value,
                            "rid": rid,
                            "field": field_path,
                            "message": f"Required field '{field_path}' not provided",
                        })
        
        if errors:
            raise MergeError(
                f"Merge failed with {len(errors)} error(s)",
                errors=errors,
            )

    def _find_resource(
        self,
        resources: List[Resource],
        rid: str,
    ) -> Resource | None:
        """Find a resource by rid."""
        for resource in resources:
            # resource.rid is a Ref (RootModel[str]), get the actual string value
            resource_rid = resource.rid.ref
            if resource_rid == rid:
                return resource
        return None

    def _set_field_value(
        self,
        resource: Resource,
        field_path: str,
        value: Any,
    ) -> None:
        """
        Set a field value in the resource config.
        
        Handles nested paths like "nested.field".
        The config is a Pydantic model, so we need to handle it properly.
        """
        if resource.config is None:
            return
        
        parts = field_path.split(".")
        
        if len(parts) == 1:
            # Direct field on config
            if hasattr(resource.config, parts[0]):
                setattr(resource.config, parts[0], value)
        else:
            # Nested field - navigate to parent
            target = resource.config
            for part in parts[:-1]:
                if hasattr(target, part):
                    target = getattr(target, part)
                else:
                    return  # Path doesn't exist
            
            # Set the final value
            if hasattr(target, parts[-1]):
                setattr(target, parts[-1], value)

    def _collect_filled_fields(
        self,
        placeholders: PlaceholderMeta,
        user_input: Dict[str, Any],
    ) -> List[str]:
        """Collect list of fields that were filled by user."""
        filled = []
        
        for cat_placeholders in placeholders.categories:
            category = cat_placeholders.category
            cat_input = user_input.get(category.value, {})
            
            for res_placeholders in cat_placeholders.resources:
                rid = res_placeholders.rid
                res_input = cat_input.get(rid, {})
                
                for placeholder in res_placeholders.placeholders:
                    field_name = placeholder.field_path.split(".")[-1]
                    if field_name in res_input:
                        filled.append(f"{category.value}.{rid}.{placeholder.field_path}")
        
        return filled


# Backwards compatibility alias
TemplateInstantiatorWithTracking = TemplateInstantiator
