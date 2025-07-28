from flask import Blueprint, jsonify, session
from webargs import fields
from shared.logger import logger
from global_utils.helpers.apiargs import from_body
from global_utils.celery_app.helpers import send_task
from global_utils.celery_app import CeleryApp
celery_app = CeleryApp().app
pipelines_bp = Blueprint("pipelines", __name__)


@pipelines_bp.route("/embed", methods=["PUT"])
@from_body({
    "data": fields.List(fields.Dict(), required=True),
    "type": fields.Str(required=True),
})
def start_pipeline(data, type):
    """
    Trigger the embedding pipeline for registered data sources.
    First calls registration task, waits for completion, then calls pipeline execution tasks.
    
    Args:
        data: List of data sources to register and process
        type: Type of data source (SLACK, DOCUMENT, etc.)
        
    Returns:
        JSON response indicating task submission status
    """
    try:
        user_session = session.get('user', {})
        current_user = user_session.get('username', 'default')
        registration_result = celery_app.send_task(
            "pipeline.pipeline_tasks.register_sources_task",
            kwargs={
                "data_list": data,
                "source_type": type.upper(),
                "upload_by": current_user
            },
            queue="registration_queue"  
        )
        
        registration_response = registration_result.get(timeout=300)  # 5 minute timeout
        registered_sources = registration_response.get("registered_sources", [])
        
        logger.info(f"Registration completed for {len(registered_sources)} sources")
        
        pipeline_tasks_submitted = 0
        for source_data in registered_sources:
            send_task(
                task_name="pipeline.pipeline_tasks.execute_pipeline_task",
                celery_queue=f"{type.lower()}_queue",
                source_type=type.upper() ,
                source_data=source_data
            )
            pipeline_tasks_submitted += 1
        
        logger.info(f"Submitted {pipeline_tasks_submitted} {type} pipeline tasks after registration")
        
        return jsonify({
            "status": "pipeline_started",
            "message": f"Registration completed and pipeline started for {len(registered_sources)} {type} sources",
            "registration_completed": True,
            "pipeline_tasks_submitted": pipeline_tasks_submitted,
            "source_count": len(registered_sources),
        }), 202
        
    except Exception as e:
        logger.error(f"Failed to start registration and pipeline flow: {str(e)}")
        return jsonify({"error": str(e)}), 500
