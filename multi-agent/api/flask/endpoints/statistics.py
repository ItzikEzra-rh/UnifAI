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
        statistics_service = container.statistics_service
        
        stats = statistics_service.get_agentic_stats(user_id)
        
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

