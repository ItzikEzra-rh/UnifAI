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
def register_sources(data, type):
    """
    Register data sources in the sources collection.
    
    Args:
        data: List of data sources to register
        type: Type of data source (SLACK or DOCUMENT)
        
    Returns:
        List of registered sources with their generated IDs.
    """
    try:
        user = session.get('user', {}).get('name', 'default')
        data_sources = register_data_sources(data, type, user)
        return jsonify({"data_sources": data_sources}), 200
    except Exception as e:
        logger.error(f"Failed to register data sources: {str(e)}")
        return jsonify({"error": str(e)}), 500


@pipelines_bp.route("/embed", methods=["PUT"])
@from_body({
    "data": fields.List(fields.Dict(), required=True),
    "type": fields.Str(required=True),
})
def start_pipeline(data, type):
    """
    Trigger the embedding pipeline for registered data sources.
    
    Args:
        data: List of data sources with their IDs and metadata
        type: Type of data source (SLACK, DOCUMENT, etc.)
        
    Returns:
        JSON response indicating task submission status
    """
    try:
        user = session.get('user', {}).get('name', 'default')
        
        # Use the general pipeline task for all source types
        source_type = type.upper()  # Convert to uppercase for consistency
        
        # Submit individual pipeline tasks for each data source
        for source_data in data:
            send_task(
                task_name="pipeline.pipeline_tasks.execute_pipeline_task",
                celery_queue="pipeline_queue",
                source_type=source_type,
                source_data=source_data,
                upload_by=user
            )
        
        logger.info(f"Submitted {len(data)} {type} sources for pipeline processing using general pipeline task")
        
        return jsonify({
            "status": "pipeline_started",
            "message": f"Embedding pipeline started for {len(data)} {type} sources",
            "task_submitted": True,
            "source_count": len(data)
        }), 202
        
    except Exception as e:
        logger.error(f"Failed to start embedding pipeline: {str(e)}")
        return jsonify({"error": str(e)}), 500
