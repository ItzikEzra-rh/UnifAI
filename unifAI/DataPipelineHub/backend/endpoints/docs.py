from flask import Blueprint, jsonify
from webargs import fields
from shared.logger import logger
from global_utils.helpers.apiargs import from_query, from_body
from global_utils.celery_app.helpers import send_task
from providers.docs import get_available_doc_list

docs_bp = Blueprint("docs", __name__)


@docs_bp.route("/available.docs.get", methods=["GET"])
def available_doc_list():
    try:
        docs = get_available_doc_list()
        return jsonify({"docs": docs}), 200
    except Exception as e:
        logger.error(f"Failed to get available docs list: {str(e)}")
        return jsonify({"error": str(e)}), 500
    
@docs_bp.route("/embed.docs", methods=["PUT"])
@from_body({
    "docs": fields.List(fields.Dict(), required=True)
})
def embed_docs(docs):
    try:
        send_task(
            task_name="data_sources.docs.docs_tasks.embed_docs_task",
            celery_queue="docs_queue",
            channel_list=docs
        )
        return jsonify({"status": "task submitted"}), 202
    except Exception as e:
        logger.error(f"Failed to submit docs embedding task: {str(e)}")
        return jsonify({"error": str(e)}), 500