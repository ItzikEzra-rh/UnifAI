"""
Template Service - Public facade for template operations.

Single Responsibility: Orchestrate template CRUD, schema generation, and instantiation.
Dependency Inversion: Depends on abstractions (repository interface, element registry).
"""
from typing import List, Dict, Any, Optional, Tuple
from uuid import uuid4
from datetime import datetime

from blueprints.models.blueprint import BlueprintDraft
from catalog.element_registry import ElementRegistry
from templates.repository.repository import TemplateRepository
from templates.models.template import (
    Template,
    PlaceholderMeta,
    TemplateMetadata,
)
from templates.schema.analyzer import PlaceholderAnalyzer
from templates.schema.generator import InputValidator
from templates.instantiation.instantiator import (
    TemplateInstantiator,
    TemplateInstantiatorWithTracking,
    InstantiationResult,
    MergeError,
)
from templates.instantiation.materializer import (
    ResourceMaterializer,
    MaterializationResult,
)


class TemplateNotFoundError(Exception):
    """Raised when template is not found."""
    
    def __init__(self, template_id: str):
        super().__init__(f"Template not found: {template_id}")
        self.template_id = template_id


class TemplateSaveError(Exception):
    """Raised when template save fails."""
    pass


class InstantiationError(Exception):
    """Raised when template instantiation fails."""
    
    def __init__(self, message: str, errors: List[Dict[str, Any]] = None):
        super().__init__(message)
        self.errors = errors or []


class TemplateService:
    """
    Public facade for template operations.
    
    Orchestrates:
    - Template CRUD operations
    - Input schema generation
    - Template instantiation
    - Blueprint and resource materialization
    
    All external interactions go through this service.
    
    Dependencies (injected):
    - TemplateRepository: Template persistence
    - ElementRegistry: Element schema lookups
    - BlueprintService (optional): For saving instantiated blueprints
    - ResourcesService (optional): For saving instantiated resources
    """

    def __init__(
        self,
        repository: TemplateRepository,
        element_registry: ElementRegistry,
        blueprint_service=None,  # Optional: BlueprintService
        resources_service=None,  # Optional: ResourcesService
    ):
        self._repo = repository
        self._element_registry = element_registry
        self._blueprint_service = blueprint_service
        self._resources_service = resources_service
        
        # Internal components
        self._analyzer = PlaceholderAnalyzer(element_registry)
        self._input_validator = InputValidator(self._analyzer)
        self._instantiator = TemplateInstantiatorWithTracking()

    # ─────────────────────────────────────────────────────────────────────
    #  Template CRUD
    # ─────────────────────────────────────────────────────────────────────
    def create_template(
        self,
        draft: BlueprintDraft,
        placeholders: PlaceholderMeta,
        metadata: Optional[TemplateMetadata] = None,
    ) -> str:
        """
        Create a new template.
        
        Args:
            draft: The template blueprint (valid BlueprintDraft)
            placeholders: Metadata about placeholder fields
            metadata: Optional template metadata
            
        Returns:
            Generated template ID
        """
        template_id = str(uuid4())
        
        template = Template(
            template_id=template_id,
            draft=draft,
            placeholders=placeholders,
            metadata=metadata or TemplateMetadata(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        return self._repo.save(template)

    def get_template(self, template_id: str) -> Template:
        """
        Get a template by ID.
        
        Raises TemplateNotFoundError if not found.
        """
        try:
            return self._repo.get(template_id)
        except KeyError:
            raise TemplateNotFoundError(template_id)

    def update_template(self, template: Template) -> bool:
        """
        Update an existing template.
        
        Returns True if modified.
        Raises TemplateNotFoundError if not found.
        """
        try:
            template.updated_at = datetime.utcnow()
            return self._repo.update(template)
        except KeyError:
            raise TemplateNotFoundError(template.template_id)

    def delete_template(self, template_id: str) -> bool:
        """
        Delete a template.
        
        Returns True if deleted.
        """
        return self._repo.delete(template_id)

    def exists(self, template_id: str) -> bool:
        """Check if template exists."""
        return self._repo.exists(template_id)

    # ─────────────────────────────────────────────────────────────────────
    #  Template Listing
    # ─────────────────────────────────────────────────────────────────────
    def list_templates(
        self,
        *,
        is_public: Optional[bool] = True,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Template]:
        """
        List templates with optional filtering.
        
        Default: returns only public templates.
        """
        return self._repo.list_templates(
            is_public=is_public,
            category=category,
            tags=tags,
            skip=skip,
            limit=limit,
        )

    def search_templates(
        self,
        query: str,
        *,
        limit: int = 20,
    ) -> List[Template]:
        """Search templates by name/description."""
        return self._repo.search(query, is_public=True, limit=limit)

    def count_templates(
        self,
        *,
        is_public: Optional[bool] = True,
        category: Optional[str] = None,
    ) -> int:
        """Count templates matching criteria."""
        return self._repo.count(is_public=is_public, category=category)

    # ─────────────────────────────────────────────────────────────────────
    #  Input Schema Generation
    # ─────────────────────────────────────────────────────────────────────
    def get_input_schema(self, template_id: str) -> Dict[str, Any]:
        """
        Get the input schema for a template as JSON Schema.
        
        Returns a complete JSON Schema with all field definitions,
        types, constraints, and $defs for complex types.
        
        The schema is generated by Pydantic from the exact field
        definitions in the element config schemas.
        """
        template = self.get_template(template_id)
        return self._analyzer.get_json_schema(template)

    def get_input_json_schema(self, template_id: str) -> Dict[str, Any]:
        """
        Get JSON Schema for template input.
        
        Alias for get_input_schema() - both return the same JSON Schema.
        """
        return self.get_input_schema(template_id)

    # ─────────────────────────────────────────────────────────────────────
    #  Input Validation
    # ─────────────────────────────────────────────────────────────────────
    def validate_input(
        self,
        template_id: str,
        user_input: Dict[str, Any],
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Validate user input against template schema.
        
        Uses the generated Pydantic model for validation.
        Returns (is_valid, errors) tuple.
        """
        template = self.get_template(template_id)
        errors = self._input_validator.get_validation_errors(template, user_input)
        return len(errors) == 0, errors

    # ─────────────────────────────────────────────────────────────────────
    #  Template Instantiation
    # ─────────────────────────────────────────────────────────────────────
    def instantiate(
        self,
        template_id: str,
        user_input: Dict[str, Any],
    ) -> BlueprintDraft:
        """
        Instantiate a template with user input.
        
        Merges user values into placeholder positions and
        returns a valid BlueprintDraft.
        
        Raises InstantiationError if instantiation fails.
        """
        template = self.get_template(template_id)
        
        try:
            return self._instantiator.instantiate(template, user_input)
        except MergeError as e:
            raise InstantiationError(str(e), errors=e.errors)
        except Exception as e:
            raise InstantiationError(f"Instantiation failed: {str(e)}")

    def instantiate_with_tracking(
        self,
        template_id: str,
        user_input: Dict[str, Any],
    ) -> InstantiationResult:
        """
        Instantiate template and return result with tracking info.
        
        Includes metadata about what fields were filled.
        """
        template = self.get_template(template_id)
        
        try:
            return self._instantiator.instantiate_with_tracking(
                template, user_input
            )
        except MergeError as e:
            raise InstantiationError(str(e), errors=e.errors)

    def preview_instantiation(
        self,
        template_id: str,
        user_input: Dict[str, Any],
    ) -> BlueprintDraft:
        """
        Preview instantiation.
        
        Returns BlueprintDraft with placeholders filled.
        """
        template = self.get_template(template_id)
        return self._instantiator.instantiate(template, user_input)

    # ─────────────────────────────────────────────────────────────────────
    #  Full Materialization (Blueprint + Resources)
    # ─────────────────────────────────────────────────────────────────────
    def materialize(
        self,
        template_id: str,
        user_id: str,
        user_input: Dict[str, Any],
        blueprint_name: Optional[str] = None,
        save_resources: bool = True,
        skip_validation: bool = False,
    ) -> Dict[str, Any]:
        """
        Instantiate template and save blueprint + resources to user's account.
        
        This is the main entry point for template usage.
        
        Flow:
        1. Instantiate template with user input
        2. Validate the resulting blueprint
        3. If save_resources=True: Save inline resources and create $refs
        4. Save blueprint to user's account
        
        Args:
            template_id: Template to instantiate
            user_id: User who owns the result
            user_input: User-provided values
            blueprint_name: Optional name override
            save_resources: If True, save resources and create $refs (default)
            skip_validation: If True, skip blueprint validation (default False)
            
        Returns:
            Dict with blueprint_id, resource_ids, and metadata
            
        Raises:
            InstantiationError: If instantiation or validation fails
            RuntimeError: If required services not configured
        """
        if self._blueprint_service is None:
            raise RuntimeError("BlueprintService not configured")
        
        # Get template and instantiate (merge placeholders)
        template = self.get_template(template_id)
        result = self._instantiator.instantiate_with_tracking(
            template, user_input
        )
        
        # Override name if provided
        if blueprint_name:
            result.blueprint.name = blueprint_name
        
        # Validate the blueprint before materialization
        if not skip_validation:
            validation_result = self._blueprint_service.validate_draft(
                result.blueprint.model_dump(mode="json")
            )
            if not validation_result.is_valid:
                # Collect validation errors using to_dict() for each failed element
                errors = [
                    elem_result.to_dict()
                    for elem_result in validation_result.element_results.values()
                    if not elem_result.is_valid
                ]
                raise InstantiationError(
                    f"Blueprint validation failed with {len(errors)} error(s)",
                    errors=errors,
                )
        
        resource_ids = []
        
        if save_resources and self._resources_service is not None:
            # Materialize resources (save inline configs, create $refs)
            materializer = ResourceMaterializer(self._resources_service)
            mat_result = materializer.materialize(result.blueprint, user_id)
            
            # Save the materialized blueprint (with $refs)
            blueprint_id = self._blueprint_service.save_draft(
                user_id=user_id,
                draft_dict=mat_result.blueprint_draft.model_dump(mode="json"),
                metadata={
                    "source": "template",
                    "template_id": template_id,
                    "template_name": template.name,
                },
            )
            resource_ids = mat_result.resource_ids
        else:
            # Save blueprint directly (inline configs)
            blueprint_id = self._blueprint_service.save_draft(
                user_id=user_id,
                draft_dict=result.blueprint.model_dump(mode="json"),
                metadata={
                    "source": "template",
                    "template_id": template_id,
                    "template_name": template.name,
                },
            )
        
        return {
            "blueprint_id": blueprint_id,
            "template_id": template_id,
            "fields_filled": result.field_count,
            "name": result.blueprint.name,
            "resources_created": len(resource_ids),
            "resource_ids": resource_ids,
        }

    # ─────────────────────────────────────────────────────────────────────
    #  Utility Methods
    # ─────────────────────────────────────────────────────────────────────
    def get_template_summary(self, template_id: str) -> Dict[str, Any]:
        """
        Get a summary of template for catalog display.
        
        Lightweight method that returns key metadata.
        """
        template = self.get_template(template_id)
        
        return {
            "template_id": template.template_id,
            "name": template.name,
            "description": template.description,
            "placeholder_count": template.placeholders.placeholder_count(),
            "category": template.metadata.category,
            "tags": template.metadata.tags,
            "version": template.metadata.version,
            "output_capabilities": template.metadata.output_capabilities,
            "author": template.metadata.author,
            "is_public": template.metadata.is_public,
            "created_at": template.created_at.isoformat(),
        }

    def list_template_summaries(
        self,
        *,
        is_public: Optional[bool] = True,
        category: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get summaries for template listing.
        
        More efficient than full template load for catalog pages.
        """
        templates = self.list_templates(
            is_public=is_public,
            category=category,
            skip=skip,
            limit=limit,
        )
        
        return [
            {
                "template_id": t.template_id,
                "name": t.name,
                "description": t.description,
                "placeholder_count": t.placeholders.placeholder_count(),
                "category": t.metadata.category,
                "tags": t.metadata.tags,
                "version": t.metadata.version,
                "output_capabilities": t.metadata.output_capabilities,
                "author": t.metadata.author,
            }
            for t in templates
        ]
