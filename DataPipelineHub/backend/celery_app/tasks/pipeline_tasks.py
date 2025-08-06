import os
import uuid
from global_utils.helpers.helpers import calculate_date_range
from pipeline.webhook_slack_pipeline_factory import WebhookSlackPipelineFactory
from pipeline.webhook_incremental_slack_pipeline_factory import WebhookIncrementalSlackPipelineFactory
from config.app_config import AppConfig
from global_utils.celery_app import CeleryApp
from pipeline.pipeline_factory import PipelineFactory
from pipeline.pipeline_executor import PipelineExecutor
from shared.source_types import (
    SlackMetadata, DocumentMetadata, SlackTypeData, DocumentTypeData,
    RegisteredSource, RegistrationResponse, PipelineExecutionResult
)
from shared.logger import logger
from config.constants import DataSource, PipelineStatus
from utils.storage.mongo.mongo_helpers import get_mongo_storage

app_config = AppConfig()
upload_folder = app_config.get("upload_folder", "")

# Initialize mongo storage for registration
mongo_storage = get_mongo_storage()

@CeleryApp().app.task(bind=True, max_retries=3, default_retry_delay=30)
def register_sources_task(self, data_list: list, source_type: str, upload_by: str = "default"):
    """
    Registration-only task that processes all data sources, creates pipeline IDs,
    and registers them in the mongo sources collection using upsert_source_summary.
    
    Supports optional user-defined metadata (e.g., settings from frontend) that gets
    stored in the type_data.user_settings field in MongoDB for later retrieval.
    
    Args:
        data_list: List of data sources to register. Each item can optionally contain
                  a 'metadata' field with user-defined settings (dateRange, communityPrivacy, etc.)
        source_type: Type of data source (SLACK, DOCUMENT, etc.)
        upload_by: User who initiated the registration
        
    Returns:
        List of registered sources with their pipeline IDs added
    """
    try:
        logger.info(f"Starting registration for {len(data_list)} {source_type} sources by user {upload_by}")
        
        registered_sources = []
        
        for instance in data_list:
            # Extract optional user-defined metadata from frontend
            user_metadata = instance.get("metadata", {})
            if user_metadata:
                logger.info(f"Processing user metadata: {user_metadata}")
            
            # Generate source_id and pipeline_id based on source type
            if source_type.upper() == DataSource.SLACK.upper_name:
                source_id = instance.get("channel_id", "")
                source_name = instance.get("channel_name", "")
                pipeline_id = f"{DataSource.SLACK.value}_{source_id}"
                
                # Create metadata object
                metadata = SlackMetadata(
                    channel_id=source_id,
                    channel_name=source_name,
                    is_private=instance.get("is_private", False),
                    upload_by=upload_by
                )
                
                date_range = user_metadata.get("dateRange")
                start_datetime, end_datetime = calculate_date_range(date_range)
                
                # Create type_data for Slack using Pydantic model
                slack_type_data = SlackTypeData(
                    is_private=instance.get("is_private", False),
                    start_timestamp=start_datetime,
                    end_timestamp=end_datetime,
                    new_messages_since_last_embedding=0,
                    webhook_active=True,  
                    **user_metadata  # Unpack user metadata into the model
                )
                type_data = slack_type_data.model_dump()
                
            elif source_type.upper() == DataSource.DOCUMENT.upper_name:
                source_id = str(uuid.uuid4())
                source_name = instance.get("source_name", "")
                doc_path = os.path.join(upload_folder, source_name)
                pipeline_id = f"{DataSource.DOCUMENT.value}_{source_id}"
                
                # Create metadata object
                metadata = DocumentMetadata(
                    doc_id=source_id,
                    doc_name=source_name,
                    doc_path=doc_path,
                    upload_by=upload_by
                )
                
                # Create type_data for Document using Pydantic model
                doc_type_data = DocumentTypeData(
                    file_type=source_name.rsplit(".", 1)[-1].lower(),
                    doc_path=doc_path,
                    page_count=0,
                    full_text="",
                    file_size=0,
                    **user_metadata  # Unpack user metadata into the model
                )
                type_data = doc_type_data.model_dump()
                
            else:
                logger.error(f"Unsupported source type: {source_type}")
                continue

            # Register source using upsert_source_summary (only type_data now)
            mongo_storage.upsert_source_summary(
                source_id=source_id,
                source_name=source_name,
                source_type=source_type.upper(),
                upload_by=upload_by,
                pipeline_id=pipeline_id,
                type_data=type_data
            )
            
            # Return only essential data needed for pipeline execution
            registered_source = RegisteredSource(
                pipeline_id=pipeline_id,
                metadata=metadata.__dict__, 
                source_type=source_type.upper(),
                upload_by=upload_by
            )
            
            registered_sources.append(registered_source.model_dump())
            metadata_info = f" with user settings: {user_metadata}" if user_metadata else ""
            logger.info(f"Registered {source_type} source: {source_name} with pipeline_id: {pipeline_id}{metadata_info}")
        
        logger.info(f"Successfully registered {len(registered_sources)} {source_type} sources with pipeline IDs")
        
        return RegistrationResponse(
            status="registration_complete",
            registered_sources=registered_sources
        ).model_dump()
        
    except Exception as e:
        logger.error(f"Registration task failed for {source_type}: {str(e)}", exc_info=True)
        raise self.retry(exc=e)

@CeleryApp().app.task(bind=True)
def execute_pipeline_task(self, source_type: str, source_data: dict):
    """
    General pipeline execution task that works with any source type.
    
    Args:
        source_type: Type of source (SLACK, DOCUMENT, etc.)
        source_data: RegisteredSource data from registration task
    """
    try:
        logger.info(f"Starting pipeline execution for {source_type} source: {source_data}")
        
        # Extract data from the clean structure
        pipeline_id = source_data.get("pipeline_id")
        metadata_dict = source_data.get("metadata")
        if not pipeline_id or not metadata_dict:
            raise ValueError("Pipeline ID or metadata not found in source_data")

        # Deserialize metadata based on source type
        if source_type.upper() == DataSource.SLACK.upper_name:
            metadata = SlackMetadata(**metadata_dict)
            
        elif source_type.upper() == DataSource.DOCUMENT.upper_name:
            metadata = DocumentMetadata(**metadata_dict)
            logger.info(f"Document path: {metadata}")
        else:
            raise ValueError(f"Unsupported source type: {source_type}")
        
        # Create factory and executor using the modular pipeline architecture
        factory = PipelineFactory.create(source_type, metadata)
        pipeline = factory.create_pipeline()
        executor = PipelineExecutor(pipeline, pipeline_id)
        
        # Execute the pipeline
        result = executor.run()
        
        logger.info(f"Pipeline execution completed successfully for {source_type}: {pipeline_id}")
        return PipelineExecutionResult(
            pipeline_id=pipeline_id,
            source_type=source_type,
            status="success",
            result=result
        ).model_dump()
        
    except Exception as e:
        logger.error(f"Pipeline execution failed for {source_type}: {str(e)}", exc_info=True)


@CeleryApp().app.task(bind=True, max_retries=3, default_retry_delay=30)
def webhook_based_incremental_slack_task(self, minimum_message_threshold: int = 5) -> dict:
    """
    Webhook-based Celery task to process incremental Slack messages based on message counters.
    
    This task:
    1. Finds all active Slack channels with new_messages_since_last_embedding > threshold
    2. For each qualifying channel, processes the new messages since last embedding
    3. Resets the message counter to 0 after successful processing
    
    Args:
        minimum_message_threshold: Minimum number of new messages to trigger embedding (default: 5)
    
    Returns:
        Dictionary containing processing results and summary
    """
    logger.info(f"Starting webhook-based incremental Slack processing (threshold: {minimum_message_threshold})")
    
    try:
        mongo_storage = get_mongo_storage()
        results = {
            "task_status": "success",
            "channels_processed": 0,
            "channels_failed": 0,
            "channels_skipped": 0,
            "total_new_messages": 0,
            "total_embeddings": 0,
            "threshold_used": minimum_message_threshold,
            "channel_results": []
        }
        
        # Get all active Slack channels with webhook monitoring enabled
        all_sources = mongo_storage.get_all_sources(DataSource.SLACK.upper_name)
        active_channels = []
        
        for source in all_sources:
            # Must be active (DONE status) and have webhook monitoring enabled
            if (source.get("status") == PipelineStatus.DONE.value and 
                source.get("type_data", {}).get("webhook_active", False)):
                
                # Check if message threshold is met
                new_messages_count = source.get("type_data", {}).get("new_messages_since_last_embedding", 0)
                if new_messages_count >= minimum_message_threshold:
                    active_channels.append(source)
        
        logger.info(f"Found {len(active_channels)} channels with ≥{minimum_message_threshold} new messages for processing")
        
        if not active_channels:
            logger.info("No channels meet the message threshold for processing")
            return results
        
        # Process each qualifying channel
        for channel in active_channels:
            channel_id = channel.get("source_id")
            channel_name = channel.get("source_name", channel_id)
            type_data = channel.get("type_data", {})
            new_messages_count = type_data.get("new_messages_since_last_embedding", 0)
            
            try:
                logger.info(f"Processing {new_messages_count} new messages for channel: {channel_name}")
                
                # Create metadata for the channel
                metadata = SlackMetadata(
                    channel_id=channel_id,
                    channel_name=channel_name or channel_id,
                    is_private=type_data.get("is_private", False),
                    upload_by=channel.get("upload_by", "system")
                )
                
                # Create webhook-based incremental pipeline factory
                pipeline_factory = WebhookIncrementalSlackPipelineFactory(metadata)
                
                # Execute the pipeline (this will handle fetching only new messages)
                executor = PipelineExecutor(pipeline_factory, channel.get("pipeline_id", f"slack_{channel_id}"))
                result = executor.run()
                
                # Reset the message counter after successful processing
                updated_type_data = type_data.copy()
                updated_type_data.update({
                    "new_messages_since_last_embedding": 0,
                    "last_embedding_timestamp": f"{__import__('datetime').datetime.now().timestamp()}",
                    "last_embedding_date": f"{__import__('datetime').datetime.now().isoformat()}",
                    "last_processed_message_count": new_messages_count
                })
                
                # Update the source with reset counter
                mongo_storage.upsert_source_summary(
                    source_id=channel_id,
                    source_name=channel_name,
                    source_type=DataSource.SLACK.upper_name,
                    upload_by=channel.get("upload_by", "system"),
                    pipeline_id=channel.get("pipeline_id", ""),
                    type_data=updated_type_data
                )
                
                channel_result = {
                    "channel_id": channel_id,
                    "channel_name": channel_name,
                    "status": "success",
                    "messages_processed": new_messages_count,
                    "counter_reset": True,
                    "processed": True
                }
                
                results["channels_processed"] += 1
                results["total_new_messages"] += new_messages_count
                results["channel_results"].append(channel_result)
                
                logger.info(f"Successfully processed {new_messages_count} messages for channel: {channel_name}, counter reset to 0")
                
            except Exception as e:
                error_msg = f"Failed to process channel {channel_name}: {str(e)}"
                logger.error(error_msg)
                
                results["channels_failed"] += 1
                results["channel_results"].append({
                    "channel_id": channel_id,
                    "channel_name": channel_name,
                    "status": "error",
                    "error": str(e),
                    "messages_processed": 0,
                    "counter_reset": False,
                    "processed": False
                })
        
        total_qualifying_channels = len(active_channels)
        logger.info(f"Webhook-based incremental processing completed: "
                   f"{results['channels_processed']}/{total_qualifying_channels} channels processed successfully, "
                   f"{results['channels_failed']} failed, "
                   f"{results['total_new_messages']} total messages processed")
        
        return results
        
    except Exception as e:
        error_msg = f"Webhook-based incremental Slack task failed: {str(e)}"
        logger.error(error_msg)
        
        return {
            "task_status": "error",
            "error": error_msg,
            "channels_processed": 0,
            "channels_failed": 0,
            "channels_skipped": 0,
            "total_new_messages": 0,
            "total_embeddings": 0,
            "threshold_used": minimum_message_threshold,
            "channel_results": []
        } 



