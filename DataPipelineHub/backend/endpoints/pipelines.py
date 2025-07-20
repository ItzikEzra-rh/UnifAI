from providers.pipelines import register_data_sources
from flask import Blueprint, jsonify, session
from utils.storage.mongo.mongo_helpers import get_mongo_storage, get_source_service
from webargs import fields
from shared.logger import logger
from global_utils.helpers.apiargs import from_query, from_body
from global_utils.celery_app.helpers import send_task
from config.constants import DataSource

pipelines_bp = Blueprint("pipelines", __name__)

@pipelines_bp.route("/register", methods=["PUT"])
@from_query({
    "data": fields.Str(required=True, data_key='data'),
    "type": fields.Str(required=True, data_key='type'),
})
def available_slack_channels(data, type):
    try:
        user = session.get('user', {}).get('name', 'default')
        data_sources = register_data_sources(data, type, user)
        return jsonify({"data_sources": data_sources}), 200
    except Exception as e:
        logger.error(f"Failed to register data sources: {str(e)}")
        return jsonify({"error": str(e)}), 500


@pipelines_bp.route("/embed", methods=["PUT"])
@from_query({
    "data": fields.Str(required=True, data_key='data'),
    "type": fields.Str(required=True, data_key='type'),
})
def start_piepline(data, type):
    try:
        # here the celery task should be called
        return jsonify({"": ""}), 200
    except Exception as e:
        logger.error(f"Failed to register data sources: {str(e)}")
        return jsonify({"error": str(e)}), 500
