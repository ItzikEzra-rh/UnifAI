"""
Template API endpoints.

Provides REST API for template operations:
- Template CRUD
- Input schema generation
- Template instantiation and materialization
"""
from flask import Blueprint, jsonify, current_app, request
from global_utils.helpers.apiargs import from_body, from_query
from webargs import fields
import logging
from typing import Optional

from templates.service import (
    TemplateNotFoundError,
    TemplateSaveError,
    InstantiationError,
)
from templates.instantiation import MaterializationError

logger = logging.getLogger(__name__)

templates_bp = Blueprint("templates", __name__)


# ─────────────────────────────────────────────────────────────────────────────
#  Template Listing & Discovery
# ─────────────────────────────────────────────────────────────────────────────
@templates_bp.route("/templates.list", methods=["GET"])
@from_query({
    "is_public": fields.Bool(data_key="isPublic", load_default=True),
    "category": fields.Str(required=False, load_default=None),
    "tags": fields.DelimitedList(fields.Str(), data_key="tags", required=False, load_default=None),
    "skip": fields.Int(load_default=0),
    "limit": fields.Int(load_default=100),
})
def list_templates(is_public, category, tags, skip, limit):
    """
    List available templates with optional filtering.
    
    Query params:
        isPublic: Filter by public status (default: true)
        category: Filter by template category
        tags: Comma-separated list of tags to filter by
        skip: Pagination offset
        limit: Max results
    """
    try:
        svc = current_app.container.template_service
        summaries = svc.list_template_summaries(
            is_public=is_public,
            category=category,
            skip=skip,
            limit=limit,
        )
        return jsonify({
            "templates": summaries,
            "count": len(summaries),
        }), 200
    except Exception as e:
        logger.exception("Error listing templates")
        return jsonify({"error": str(e)}), 500


@templates_bp.route("/templates.search", methods=["GET"])
@from_query({
    "query": fields.Str(data_key="q", required=True),
    "limit": fields.Int(load_default=20),
})
def search_templates(query, limit):
    """
    Search templates by name/description.
    
    Query params:
        q: Search query
        limit: Max results
    """
    try:
        svc = current_app.container.template_service
        templates = svc.search_templates(query=query, limit=limit)
        summaries = [
            {
                "template_id": t.template_id,
                "name": t.name,
                "description": t.description,
                "placeholder_count": t.placeholders.placeholder_count(),
                "category": t.metadata.category,
                "tags": t.metadata.tags,
            }
            for t in templates
        ]
        return jsonify({
            "templates": summaries,
            "count": len(summaries),
        }), 200
    except Exception as e:
        logger.exception("Error searching templates")
        return jsonify({"error": str(e)}), 500


@templates_bp.route("/templates.count", methods=["GET"])
@from_query({
    "is_public": fields.Bool(data_key="isPublic", load_default=True),
    "category": fields.Str(required=False, load_default=None),
})
def count_templates(is_public, category):
    """
    Count templates matching criteria.
    """
    try:
        svc = current_app.container.template_service
        count = svc.count_templates(is_public=is_public, category=category)
        return jsonify({"count": count}), 200
    except Exception as e:
        logger.exception("Error counting templates")
        return jsonify({"error": str(e)}), 500


# ─────────────────────────────────────────────────────────────────────────────
#  Template CRUD
# ─────────────────────────────────────────────────────────────────────────────
@templates_bp.route("/template.get", methods=["GET"])
@from_query({
    "template_id": fields.Str(data_key="templateId", required=True),
})
def get_template(template_id):
    """
    Get a template by ID.
    """
    try:
        svc = current_app.container.template_service
        template = svc.get_template(template_id)
        return jsonify(template.model_dump(mode="json")), 200
    except TemplateNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        logger.exception(f"Error getting template {template_id}")
        return jsonify({"error": str(e)}), 500


@templates_bp.route("/template.summary.get", methods=["GET"])
@from_query({
    "template_id": fields.Str(data_key="templateId", required=True),
})
def get_template_summary(template_id):
    """
    Get a template summary for catalog display.
    
    Lightweight endpoint for listing views.
    """
    try:
        svc = current_app.container.template_service
        summary = svc.get_template_summary(template_id)
        return jsonify(summary), 200
    except TemplateNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        logger.exception(f"Error getting template summary {template_id}")
        return jsonify({"error": str(e)}), 500


@templates_bp.route("/template.create", methods=["POST"])
@from_body({
    "draft": fields.Dict(required=True),
    "placeholders": fields.Dict(required=True),
    "metadata": fields.Dict(required=False, load_default=lambda: {}),
})
def create_template(draft, placeholders, metadata):
    """
    Create a new template.
    
    Body:
        draft: The template blueprint (BlueprintDraft format)
        placeholders: Placeholder metadata (PlaceholderMeta format)
        metadata: Optional template metadata
    """
    try:
        from blueprints.models.blueprint import BlueprintDraft
        from templates.models.template import PlaceholderMeta, TemplateMetadata
        
        svc = current_app.container.template_service
        
        # Parse models
        draft_model = BlueprintDraft(**draft)
        placeholders_model = PlaceholderMeta(**placeholders)
        metadata_model = TemplateMetadata(**metadata) if metadata else None
        
        template_id = svc.create_template(
            draft=draft_model,
            placeholders=placeholders_model,
            metadata=metadata_model,
        )
        
        return jsonify({
            "status": "success",
            "template_id": template_id,
        }), 201
    except ValueError as e:
        return jsonify({"error": f"Invalid data: {e}"}), 400
    except Exception as e:
        logger.exception("Error creating template")
        return jsonify({"error": str(e)}), 500


@templates_bp.route("/template.delete", methods=["DELETE"])
@from_query({
    "template_id": fields.Str(data_key="templateId", required=True),
})
def delete_template(template_id):
    """
    Delete a template by ID.
    """
    try:
        svc = current_app.container.template_service
        
        if not svc.exists(template_id):
            return jsonify({
                "status": "error",
                "error": f"Template '{template_id}' not found",
            }), 404
        
        deleted = svc.delete_template(template_id)
        
        if deleted:
            return jsonify({
                "status": "success",
                "message": f"Template '{template_id}' deleted",
            }), 200
        else:
            return jsonify({
                "status": "error",
                "error": "Failed to delete template",
            }), 500
    except Exception as e:
        logger.exception(f"Error deleting template {template_id}")
        return jsonify({"error": str(e)}), 500


# ─────────────────────────────────────────────────────────────────────────────
#  Input Schema
# ─────────────────────────────────────────────────────────────────────────────
@templates_bp.route("/template.schema.get", methods=["GET"])
@from_query({
    "template_id": fields.Str(data_key="templateId", required=True),
})
def get_template_schema(template_id):
    """
    Get the input schema for a template.
    
    Returns the JSON Schema with all field definitions, types, and constraints.
    """
    try:
        svc = current_app.container.template_service
        schema = svc.get_input_schema(template_id)
        return jsonify(schema), 200
    except TemplateNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        logger.exception(f"Error getting template schema {template_id}")
        return jsonify({"error": str(e)}), 500


@templates_bp.route("/template.jsonschema.get", methods=["GET"])
@from_query({
    "template_id": fields.Str(data_key="templateId", required=True),
})
def get_template_json_schema(template_id):
    """
    Get JSON Schema for template input.
    
    Returns standard JSON Schema format for form generation.
    """
    try:
        svc = current_app.container.template_service
        json_schema = svc.get_input_json_schema(template_id)
        return jsonify(json_schema), 200
    except TemplateNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        logger.exception(f"Error getting template JSON schema {template_id}")
        return jsonify({"error": str(e)}), 500


# ─────────────────────────────────────────────────────────────────────────────
#  Validation
# ─────────────────────────────────────────────────────────────────────────────
@templates_bp.route("/template.input.validate", methods=["POST"])
@from_body({
    "template_id": fields.Str(data_key="templateId", required=True),
    "input": fields.Dict(required=True),
})
def validate_template_input(template_id, input):
    """
    Validate user input against template schema.
    
    Returns validation result with any errors.
    """
    try:
        svc = current_app.container.template_service
        is_valid, errors = svc.validate_input(template_id, input)
        
        return jsonify({
            "is_valid": is_valid,
            "errors": errors,
        }), 200
    except TemplateNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        logger.exception(f"Error validating template input {template_id}")
        return jsonify({"error": str(e)}), 500


# ─────────────────────────────────────────────────────────────────────────────
#  Instantiation
# ─────────────────────────────────────────────────────────────────────────────
@templates_bp.route("/template.preview", methods=["POST"])
@from_body({
    "template_id": fields.Str(data_key="templateId", required=True),
    "input": fields.Dict(required=True),
})
def preview_template(template_id, input):
    """
    Preview template instantiation.
    
    Returns merged BlueprintDraft for preview purposes.
    """
    try:
        svc = current_app.container.template_service
        preview = svc.preview_instantiation(template_id, input)
        return jsonify(preview.model_dump(mode="json")), 200
    except TemplateNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except InstantiationError as e:
        return jsonify({
            "error": str(e),
            "errors": e.errors,
        }), 400
    except Exception as e:
        logger.exception(f"Error previewing template {template_id}")
        return jsonify({"error": str(e)}), 500


@templates_bp.route("/template.instantiate", methods=["POST"])
@from_body({
    "template_id": fields.Str(data_key="templateId", required=True),
    "input": fields.Dict(required=True),
})
def instantiate_template(template_id, input):
    """
    Instantiate a template with user input.
    
    Returns a valid BlueprintDraft without saving.
    """
    try:
        svc = current_app.container.template_service
        blueprint = svc.instantiate(template_id, input)
        return jsonify(blueprint.model_dump(mode="json")), 200
    except TemplateNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except InstantiationError as e:
        return jsonify({
            "error": str(e),
            "errors": e.errors,
        }), 400
    except Exception as e:
        logger.exception(f"Error instantiating template {template_id}")
        return jsonify({"error": str(e)}), 500


@templates_bp.route("/template.materialize", methods=["POST"])
@from_body({
    "template_id": fields.Str(data_key="templateId", required=True),
    "user_id": fields.Str(data_key="userId", required=True),
    "input": fields.Dict(required=True),
    "blueprint_name": fields.Str(data_key="blueprintName", required=False, load_default=None),
    "skip_validation": fields.Bool(data_key="skipValidation", required=False, load_default=False),
})
def materialize_template(template_id, user_id, input, blueprint_name=None, skip_validation=False):
    """
    Instantiate template and save blueprint to user's account.
    
    This is the main entry point for template usage.
    
    Args:
        templateId: Template to instantiate
        userId: User who owns the result
        input: User-provided values for placeholders
        blueprintName: Optional name override
        skipValidation: If true, skip blueprint validation (default false)
    
    Returns:
        blueprint_id: ID of the saved blueprint
        template_id: Source template ID
        fields_filled: Number of fields that were filled
        name: Blueprint name
    """
    try:
        svc = current_app.container.template_service
        result = svc.materialize(
            template_id=template_id,
            user_id=user_id,
            user_input=input,
            blueprint_name=blueprint_name,
            skip_validation=skip_validation,
        )
        return jsonify({
            "status": "success",
            **result,
        }), 201
    except TemplateNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except InstantiationError as e:
        return jsonify({
            "error": str(e),
            "errors": e.errors,
        }), 400
    except MaterializationError as e:
        return jsonify({
            "error": str(e),
            "errors": e.errors,
        }), 400
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        logger.exception(f"Error materializing template {template_id}")
        return jsonify({"error": str(e)}), 500
