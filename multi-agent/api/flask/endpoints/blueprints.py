from flask import Blueprint, jsonify, current_app, request
from global_utils.helpers.apiargs import from_body, from_query
from webargs import fields
import yaml
from werkzeug.exceptions import BadRequest

blueprints_bp = Blueprint("blueprints", __name__)


@blueprints_bp.route("/available.blueprints.get", methods=["GET"])
@from_query({
    "user_id": fields.Str(data_key="userId", required=True)
})
def available_doc_list(user_id):
    try:
        svc = current_app.container.blueprint_service
        return jsonify(svc.list_draft_docs(user_id=user_id)), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@blueprints_bp.route("/available.blueprints.resolved.get", methods=["GET"])
@from_query({
    "user_id": fields.Str(data_key="userId", required=True)
})
def available_resolved_doc_list(user_id):
    try:
        svc = current_app.container.blueprint_service
        return jsonify(svc.list_resolved_docs(user_id=user_id)), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@blueprints_bp.route("/blueprint.save", methods=["POST"])
@from_body({
    "blueprint_raw": fields.Str(data_key="blueprintRaw", required=False),  # optional for non-JSON/YAML raw
    "user_id": fields.Str(data_key="userId", required=False, load_default="alice")
})
def save_blueprint(blueprint_raw=None, user_id="alice"):
    try:
        # Case 1: JSON body with field 'blueprintRaw'
        if blueprint_raw:
            raw_text = blueprint_raw

        # Case 2: Raw text body (YAML or JSON), e.g., Content-Type: application/x-yaml or text/plain
        elif request.content_type and (
                "yaml" in request.content_type or request.content_type.startswith("text/plain")
        ):
            raw_text = request.data.decode("utf-8")

        # Case 3: form-data file upload
        elif "blueprint_raw" in request.files:
            file = request.files["blueprint_raw"]
            raw_text = file.read().decode("utf-8")

        # Case 4: form-data string field
        elif "blueprint_raw" in request.form:
            raw_text = request.form["blueprint_raw"]

        else:
            raise BadRequest("Missing blueprint data in request")

        # Parse the YAML or JSON string
        try:
            parsed = yaml.safe_load(raw_text)
            if not isinstance(parsed, dict):
                raise ValueError("Parsed blueprint must be a dictionary.")
        except Exception as e:
            raise BadRequest(f"Invalid blueprint format: {e}")

        # Save using service
        svc = current_app.container.blueprint_service
        blueprint_id = svc.save_draft(user_id=user_id, draft_dict=parsed)

        return jsonify({
            "status": "success",
            "blueprint_id": blueprint_id
        }), 201

    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


@blueprints_bp.route("/blueprint.info.get", methods=["GET"])
@from_query({
    "blueprint_id": fields.Str(data_key="blueprintId", required=True)
})
def get_blueprint_info(blueprint_id):
    """
    Get blueprint information.
    """
    try:
        svc = current_app.container.blueprint_service
        info = svc.get_blueprint_info(blueprint_id)
        return jsonify(info), 200
    except KeyError:
        return jsonify({
            "error": "Blueprint not found"
        }), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@blueprints_bp.route("/blueprint.draft.schema.get", methods=["GET"])
def blueprint_draft_schema_get():
    """
    Returns the schema for blueprint drafts.
    """
    try:
        svc = current_app.container.blueprint_service
        schema = svc.get_draft_schema()
        return jsonify(schema), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@blueprints_bp.route("/remove.blueprint", methods=["DELETE"])
@from_query({
    "blueprint_id": fields.Str(data_key="blueprintId", required=True)
})
def remove_blueprint(blueprint_id):
    """
    Delete a blueprint by its ID.
    """
    try:
        svc = current_app.container.blueprint_service
        
        # Check if blueprint exists before attempting deletion
        if not svc.exists(blueprint_id):
            return jsonify({
                "status": "error",
                "error": f"Blueprint with ID '{blueprint_id}' not found"
            }), 404
        
        # Attempt to delete the blueprint
        deleted = svc.delete(blueprint_id)
        
        if deleted:
            return jsonify({
                "status": "success",
                "message": f"Blueprint '{blueprint_id}' deleted successfully"
            }), 200
        else:
            return jsonify({
                "status": "error",
                "error": f"Failed to delete blueprint '{blueprint_id}'"
            }), 500
            
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


@blueprints_bp.route("/public_usage_scope", methods=["PUT"])
@from_body({
    "blueprint_id": fields.Str(data_key="blueprintId", required=True),
    "public_usage_scope": fields.Bool(required=True),
    "user_id": fields.Str(data_key="userId", required=True),
})
def set_public_usage_scope(blueprint_id, public_usage_scope, user_id):
    """
    Set the public_usage_scope (True/False) of a blueprint.
    Validates the blueprint can be loaded, resolved, and compiled before enabling public usage.
    """
    try:
        svc = current_app.container.blueprint_service
        
        if public_usage_scope:
            session_svc = current_app.container.session_service
            session_svc.validate_blueprint(user_id=user_id, blueprint_id=blueprint_id)
        
        success = svc.set_public_usage_scope(blueprint_id=blueprint_id, public_usage_scope=public_usage_scope)
        
        if not success:
            return jsonify({
                "error": "Failed to update public_usage_scope",
                "error_type": "UPDATE_FAILED",
                "blueprint_id": blueprint_id
            }), 500
        
        return jsonify({"status": "success"}), 200
        
    except KeyError as e:
        return jsonify({
            "error": "Blueprint not found",
            "error_type": "BLUEPRINT_NOT_FOUND",
            "blueprint_id": blueprint_id
        }), 404
    except ValueError as e:
        return jsonify({
            "error": str(e),
            "error_type": "INVALID_PUBLIC_USAGE_SCOPE",
            "blueprint_id": blueprint_id
        }), 400
    except Exception as e:
        return jsonify({
            "error": str(e),
            "error_type": "VALIDATION_ERROR",
            "blueprint_id": blueprint_id
        }), 400


@blueprints_bp.route("/public_usage_scope", methods=["GET"])
@from_query({
    "blueprint_id": fields.Str(data_key="blueprintId", required=True),
})
def get_public_usage_scope(blueprint_id):
    """
    Get the current public_usage_scope of a blueprint.
    """
    try:
        svc = current_app.container.blueprint_service
        result = svc.get_public_usage_scope(blueprint_id)
        return jsonify(result), 200
    except KeyError:
        return jsonify({
            "error": "Blueprint not found",
            "error_type": "BLUEPRINT_NOT_FOUND",
            "blueprint_id": blueprint_id
        }), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@blueprints_bp.route("/validate", methods=["GET"])
@from_query({
    "blueprint_id": fields.Str(data_key="blueprintId", required=True),
})
def validate_blueprint(blueprint_id):
    """
    Validate a blueprint by resolving it and checking if it can be compiled.
    Returns blueprint information and ownership details.
    """
    try:
        svc = current_app.container.blueprint_service
        result = svc.validate_blueprint(blueprint_id)
        
        if not result.get("valid", False):
            return jsonify({
                **result,
                "error_type": "BLUEPRINT_INVALID" if result.get("error") != "Blueprint not found" else "BLUEPRINT_NOT_FOUND"
            }), 400
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
