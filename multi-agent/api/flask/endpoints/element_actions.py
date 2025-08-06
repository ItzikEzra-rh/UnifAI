from flask import Blueprint, jsonify, current_app
from global_utils.helpers.apiargs import from_body, from_query
from webargs import fields
from pydantic import ValidationError

catalog_actions_bp = Blueprint("catalog_actions", __name__)


@catalog_actions_bp.route("/element.actions.list", methods=["GET"])
@from_query({
    "category": fields.Str(required=True),
    "element_type": fields.Str(data_key="elementType", required=True)
})
def list_element_actions(category, element_type):
    """
    List all actions available for a specific element type and category.
    
    Query parameters:
    - category: Element category (e.g., "provider", "llm")
    - elementType: Element type (e.g., "mcp_server_client", "openai")
    
    Response format:
    {
        "actions": [
            {
                "name": "validate_connection",
                "description": "Validate that the MCP server endpoint is reachable",
                "action_type": "validation",
                "input_schema": {...},
                "output_schema": {...}
            }
        ],
        "total_actions": 2
    }
    """
    try:
        element_actions_service = current_app.container.element_actions_service
        actions_metadata = element_actions_service.get_element_actions_metadata(category, element_type)
        
        return jsonify({
            "actions": actions_metadata,
            "total_actions": len(actions_metadata)
        }), 200
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@catalog_actions_bp.route("/element.action.execute", methods=["POST"])
@from_body({
    "category": fields.Str(required=True),
    "element_type": fields.Str(data_key="elementType", required=True),
    "action_name": fields.Str(data_key="actionName", required=True),
    "input_data": fields.Dict(data_key="inputData", required=False, load_default={})
})
def execute_element_action(category, element_type, action_name, input_data):
    """
    Execute a specific action for an element type (synchronously).
    Input is validated explicitly before execution.
    
    Request body:
    {
        "category": "provider",
        "elementType": "mcp_server_client", 
        "actionName": "validate_connection",
        "inputData": {
            "sse_endpoint": "http://localhost:3000/sse"
        }
    }
    
    Response format:
    {
        "success": true,
        "message": "Connection successful",
        "is_reachable": true,
        "response_time_ms": 125.5
    }
    """
    try:
        element_actions_service = current_app.container.element_actions_service
        
        # First validate the input explicitly
        element_actions_service.validate_action_input(category, element_type, action_name, input_data)
        
        # Then execute the action
        result = element_actions_service.execute_action_sync(category, element_type, action_name, input_data)
        
        return jsonify(result), 200
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except ValidationError as e:
        return jsonify({
            "error": "Input validation failed",
            "details": e.errors()
        }), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500