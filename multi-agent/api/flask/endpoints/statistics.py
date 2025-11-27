from flask import Blueprint, jsonify, current_app
from global_utils.helpers.apiargs import from_query
from webargs import fields
from typing import Dict, Any, List

statistics_bp = Blueprint("statistics", __name__)


@statistics_bp.route("/stats.get", methods=["GET"])
@from_query({
    "user_id": fields.Str(data_key="userId", required=True),
})
def get_agentic_stats(user_id):
    """
    Get aggregated statistics for agentic features.
    Returns all stats in a single response for optimal performance.
    """
    try:
        container = current_app.container
        
        # Get services
        blueprint_service = container.blueprint_service
        session_service = container.session_service
        resources_service = container.resources_service
        
        # Get counts using optimized queries
        total_workflows = blueprint_service.count(user_id=user_id)
        active_sessions = len(session_service.get_user_blueprints(user_id))
        blueprint_session_counts = session_service.get_user_blueprint_session_counts(user_id)
        
        # Get resource aggregation using MongoDB aggregation
        resource_repo = resources_service._store._repo
        resources_by_category = resource_repo.aggregate_by_category(user_id)
        
        # Get total resources count
        total_resources = resource_repo.count(user_id, {})
        
        # Format response
        stats = {
            "totalWorkflows": total_workflows,
            "activeSessions": active_sessions,
            "totalResources": total_resources,
            "blueprintSessionCounts": blueprint_session_counts,
            "resourcesByCategory": resources_by_category
        }
        
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

