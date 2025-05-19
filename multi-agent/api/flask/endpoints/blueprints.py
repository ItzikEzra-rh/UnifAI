from flask import Blueprint, jsonify, current_app
from webargs import fields
from global_utils.helpers.apiargs import from_query, from_body
from global_utils.celery_app.helpers import send_task
from providers.blueprints import get_blueprints_list

blueprints_bp = Blueprint("blueprints", __name__)


@blueprints_bp.route("/available.blueprints.get", methods=["GET"])
def available_doc_list():
    try:
        svc = current_app.container.blueprint_service
        return jsonify(svc.list_dicts()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
