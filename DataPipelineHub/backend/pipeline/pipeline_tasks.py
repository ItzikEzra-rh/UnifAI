from global_utils.celery_app import CeleryApp
from pipeline.pipeline_factory import PipelineFactory
from pipeline.pipeline_executor import PipelineExecutor
from pipeline.types import SlackMetadata, DocumentMetadata
from shared.logger import logger
from config.constants import DataSource

# Import the concrete factories to ensure they register themselves
from pipeline.slack_pipeline_factory import SlackPipelineFactory
from pipeline.doc_pipeline_factory import DocumentPipelineFactory

@CeleryApp().app.task(bind=True, max_retries=5, default_retry_delay=60)
def execute_pipeline_task(self, source_type: str, source_data: dict, upload_by: str = "default"):
    """
    General pipeline execution task that works with any source type.
    
    Args:
        source_type: Type of source (SLACK, DOCUMENT, etc.)
        source_data: Data for creating the metadata object
        upload_by: User who initiated the pipeline
    """
    try:
        logger.info(f"Starting pipeline execution for {source_type} source: {source_data}")
        
        # Create metadata object based on source type
        if source_type == DataSource.SLACK.upper_name:
            metadata = SlackMetadata(
                channel_id=source_data.get("channel_id", ""),
                channel_name=source_data.get("channel_name", ""),
                is_private=source_data.get("is_private", False)
            )
            pipeline_id = f"slack_{metadata.channel_id}"
            
        elif source_type == DataSource.DOCUMENT.upper_name:
            metadata = DocumentMetadata(
                doc_id=source_data.get("source_id", ""),
                doc_name=source_data.get("source_name", ""),
                doc_path=source_data.get("doc_path", ""),
                upload_by=upload_by
            )
            pipeline_id = f"doc_{metadata.doc_id}"
            
        else:
            raise ValueError(f"Unsupported source type: {source_type}")
        
        # Create factory and executor using the modular pipeline architecture
        factory = PipelineFactory.create(source_type, metadata)
        executor = PipelineExecutor(factory, pipeline_id)
        
        # Execute the pipeline
        result = executor.run()
        
        logger.info(f"Pipeline execution completed successfully for {source_type}: {pipeline_id}")
        return {
            "pipeline_id": pipeline_id,
            "source_type": source_type,
            "status": "success",
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Pipeline execution failed for {source_type}: {str(e)}", exc_info=True)
        raise self.retry(exc=e) 