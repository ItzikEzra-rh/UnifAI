from dataclasses import asdict
import time
from pipeline.pipeline_repository import PipelineRepository
from pipeline.pipeline_executor import PipelineExecutor
from pipeline.pipeline_factory import PipelineFactory
from pipeline.types import SlackMetadata
import pymongo
from data_sources.slack.slack_config_manager import SlackConfigManager
from data_sources.slack.slack_connector import SlackConnector
from data_sources.slack.slack_data_processor import SlackProcessor
from data_sources.slack.slack_chunker_strategy import SlackChunkerStrategy
from data_sources.slack.slack_pipeline_scheduler import SlackDataPipeline
from config.constants import DataSource
from utils.storage.mongo.mongo_helpers import get_mongo_storage
from utils.storage.storage_manager import StorageManager
from utils.embedding.embedding_generator_factory import EmbeddingGeneratorFactory
from utils.storage.vector_storage_factory import VectorStorageFactory
from shared.logger import logger
from global_utils.utils.util import get_mongo_url
from utils.storage.qdrant_storage import QdrantStorage

def _get_configured_connector() -> SlackConnector:
    config_manager = SlackConfigManager()
    config_manager.set_project_tokens(
        project_id="example-project",
        bot_token="xoxb-2253118358-8783454711008-dwnxf7cPBpeVLlLw8KMurohb",
        user_token="xoxb-2253118358-8783454711008-dwnxf7cPBpeVLlLw8KMurohb"
    )
    config_manager.set_default_project("example-project")
    return SlackConnector(config_manager)

def fetch_available_slack_channels():
    connector = _get_configured_connector()
    if connector.authenticate():
        return connector.fetch_available_slack_channels()
    else:
        raise RuntimeError("Slack authentication failed")

def get_available_slack_channels(channel_types: str, cursor: str = "", limit: int = 50):
    connector = _get_configured_connector()
    if connector.authenticate():
        return connector.get_available_slack_channels(types=channel_types, cursor=cursor, limit=limit)
    else:
        raise RuntimeError("Slack authentication failed")

def embed_slack_channel(channel_list: str, upload_by: str = "default"):
    results = []

    for ch in channel_list:
        # Normalize incoming metadata to SlackMetadata
        if isinstance(ch, SlackMetadata):
            meta = ch
        elif isinstance(ch, dict):
            meta = SlackMetadata(
                channel_id=ch.get("channel_id", ""),
                channel_name=ch.get("channel_name", ""),
                is_private=ch.get("is_private", False)
            )
        else:
            meta = SlackMetadata(channel_id=str(ch))

        try:
            # Lookup and build the factory for this source_type
            factory = PipelineFactory.create(DataSource.SLACK.upper_name, meta)
            executor = PipelineExecutor(factory, pipeline_id=f"slack_{meta.channel_id}")
            pipeline_result = executor.run()

            results.append({
                "channel_id": meta.channel_id,
                "status": "success",
                "result": pipeline_result
            })

        except Exception as exc:
            # Capture error per-channel but continue processing others
            results.append({
                "channel_id": meta.channel_id,
                "status": "error",
                "error": str(exc)
            })

    return {
        "upload_by": upload_by,
        "results": results
    }


def embed_slack_channels_flow(channel_list, upload_by="default"):
    """
    Slack embedding flow function using the SlackEmbeddingService.
    """
    connector = _get_configured_connector()
    if not connector.authenticate():
        raise RuntimeError("Slack authentication failed")
    
    mongo_client   = pymongo.MongoClient(get_mongo_url())
    slack_pipeline = SlackDataPipeline(mongo_client, logger=logger)
    
    processor = SlackProcessor()
    chunker = SlackChunkerStrategy(max_tokens_per_chunk=500, overlap_tokens=50, time_window_seconds=300)
    
    embedding_config = {
        "type": "sentence_transformer",
        "model_name": "all-MiniLM-L6-v2",
        "batch_size": 32
    }
    embedding_generator = EmbeddingGeneratorFactory.create(embedding_config)
        # QdrantStorage via factor  y
    storage_config = {
        "type": "qdrant",
        "collection_name": "slack_data", 
        "embedding_dim": embedding_generator.embedding_dim
        # URL and port will come from app_config via VectorStorageFactory
    }
    qstore = VectorStorageFactory.create(storage_config)
    qstore.initialize()
    mongo_storage= get_mongo_storage()
        # Cast to QdrantStorage since we know it's a Qdrant instance
    from utils.storage.qdrant_storage import QdrantStorage
    qdrant_store = qstore if isinstance(qstore, QdrantStorage) else None
    if not qdrant_store:
        raise RuntimeError("Expected QdrantStorage instance")
    
        # Wrap Qdrant + MongoStorage in a manager
    # manager = StorageManager(qdrant_store, mongo_storage)

    response = []
    for channel in channel_list:
        cid  = channel["channel_id"]
        cname= channel["channel_name"]

        # 1️⃣ Register & start monitoring
        pipeline_id = slack_pipeline.process_slack_channel(cid, cname)
        slack_pipeline.monitor.start_log_monitoring(target_logger=logger, pipeline_id=f"slack_{cid}")

        # 2️⃣ Register channel in source data collection IMMEDIATELY
        try:
            # Create type_data for Slack (only source-specific data)
            initial_type_data = {
                "is_private": channel["is_private"],
                "message_count": 0,
            }

            # Register the source immediately with initial data
            mongo_storage.upsert_source_summary(
                source_id=cid,
                source_name=cname,
                source_type="SLACK",
                upload_by=upload_by,
                pipeline_id=pipeline_id,
                type_data=initial_type_data
            )

            # 3️⃣ Fetch messages first
            messages, thread_msgs = connector.get_conversations_history(cid) # done
            
            # Update source with message count immediately after fetching
            fetched_type_data = {
                "is_private": channel["is_private"],
                "message_count": len(messages),
            }

            # Update source with message count
            mongo_storage.upsert_source_summary(
                source_id=cid,
                source_name=cname,
                source_type="SLACK",
                upload_by=upload_by,
                pipeline_id=pipeline_id,
                type_data=fetched_type_data
            )
            
            # 4️⃣ Process, chunk, embed
            processed_main  = processor.process(messages,  channel_name=cname)
            processed_threads = [processor.process(t, channel_name=cname) for t in thread_msgs]

            all_chunks   = chunker.chunk_content(processed_main) + \
                           [chunk for t in processed_threads for chunk in t]
            
            # Add source_id to all chunks for Qdrant filtering/deletion
            for chunk in all_chunks:
                if "metadata" not in chunk:
                    chunk["metadata"] = {}
                chunk["metadata"]["source_id"] = cid
                chunk["metadata"]["source_type"] = "SLACK"
                # Ensure chunk_index for easier identification
                if "chunk_index" not in chunk["metadata"]:
                    chunk["metadata"]["chunk_index"] = len([c for c in all_chunks if c is chunk])
            
            embeddings   = embedding_generator.generate_embeddings(all_chunks)

            # 5️⃣ Build summary
            if hasattr(slack_pipeline.slack_monitor, "get_api_calls"):
                slack_api_calls = slack_pipeline.slack_monitor.get_api_calls(pipeline_id)
            else:
                slack_api_calls = 0
            start = time.time()

            # 6️⃣ Store embeddings in Qdrant
            enriched = embedding_generator.generate_embeddings(all_chunks)
            qstore.store_embeddings(enriched)

            # 7️⃣ Update source with final data (only source-specific)
            final_type_data = {
                "is_private": channel["is_private"],
                "message_count": len(messages),
            }

            # Update the source with final processing results
            mongo_storage.upsert_source_summary(
                source_id=cid,
                source_name=cname,
                source_type="SLACK",
                upload_by=upload_by,
                pipeline_id=pipeline_id,
                type_data=final_type_data
            )

            # 8️⃣ Mark success in monitor
            slack_pipeline.monitor.finish_log_monitoring()

            response.append({
              "channel":     cname,
              "status":      "success",
              "chunks_stored": len(all_chunks)
            })

        except Exception as e:
            # 9️⃣ On error, record it and update source status
            logger.error(f"Error embedding {cname}: {e}")
            if pipeline_id:
                slack_pipeline.monitor.record_error(pipeline_id, str(e))
            
            # Update source with error (only source-specific data)
            error_type_data = {
                "is_private": channel["is_private"],
                "message_count": 0,
            }

            mongo_storage.upsert_source_summary(
                source_id=cid,
                source_name=cname,
                source_type="SLACK",
                upload_by=upload_by,
                pipeline_id=pipeline_id,
                type_data=error_type_data
            )
            
            response.append({
              "channel":     cname,
              "status":      "failed",
              "error":       str(e)
            })

    return response

def count_channel_chunks(channel_name: str) -> int:
    storage_config = {
        "type": "qdrant",
        "collection_name": "slack_data",
        "embedding_dim": 384  # Must match embedding model
        # URL and port will come from app_config via VectorStorageFactory
    }
    vector_storage = VectorStorageFactory.create(storage_config)
    vector_storage.initialize()

    return vector_storage.count(filters={"metadata.channel_name": channel_name})

def get_best_match_results(query: str, top_k_results: int = 5, scope: str = "public", logged_in_user: str = "default"):

    embedding_config = {
        "type": "sentence_transformer",
        "model_name": "all-MiniLM-L6-v2",
        "batch_size": 32
    }
    embedding_generator = EmbeddingGeneratorFactory.create(embedding_config)
    
    # Create vector storage
    storage_config = {
        "type": "qdrant",
        "collection_name": "slack_data",
        "embedding_dim": embedding_generator.embedding_dim
        # URL and port will come from app_config via VectorStorageFactory
    }
    vector_storage = VectorStorageFactory.create(storage_config)
    vector_storage.initialize()
    
    query_embedding = embedding_generator.generate_query_embedding(query)
    
    search_results = vector_storage.search(
        query_embedding=query_embedding,
        top_k=top_k_results,
        filters={"upload_by": logged_in_user} if scope == "private" else {}
    )

    return search_results

def _initialize_storage_manager():
    """Initialize and return storage manager for operations."""
    embedding_config = {
        "type": "sentence_transformer", 
        "model_name": "all-MiniLM-L6-v2",
        "batch_size": 32
    }
    embedding_generator = EmbeddingGeneratorFactory.create(embedding_config)
    
    storage_config = {
        "type": "qdrant",
        "collection_name": "slack_data", 
        "embedding_dim": embedding_generator.embedding_dim
        # URL and port will come from app_config via VectorStorageFactory
    }
    qdrant_storage = VectorStorageFactory.create(storage_config)
    qdrant_storage.initialize()
    
    mongo_storage = get_mongo_storage()
    
    from utils.storage.qdrant_storage import QdrantStorage
    from utils.storage.storage_manager import StorageManager
    
    qdrant_store = qdrant_storage if isinstance(qdrant_storage, QdrantStorage) else None
    if not qdrant_store:
        raise RuntimeError("Expected QdrantStorage instance")
    
    return StorageManager(qdrant_store, mongo_storage)

def delete_slack_channel(channel_id: str) -> dict:
    """
    Delete a slack channel from both MongoDB and Qdrant storage.
    
    Args:
        channel_id: The ID of the channel to delete
        
    Returns:
        dict: Result information about the deletion
        
    Raises:
        Exception: If deletion fails
    """
    try:
        # Initialize storage manager
        storage_manager = _initialize_storage_manager()
        
        # Delete using the general storage manager method
        result = storage_manager.delete_source(channel_id, DataSource.SLACK.upper_name)
        
        # Convert to the expected format for backward compatibility
        summary = result.get("summary", {})
        return {
            "success": result.get("success", False),
            "result": {
                "channel_id": result.get("source_id"),
                "channel_name": result.get("source_name"),
                "qdrant_embeddings_deleted": summary.get("embeddings_deleted", 0),
                "mongo_source_deleted": summary.get("source_deleted", False),
                "mongo_pipelines_deleted": summary.get("pipelines_deleted", 0)
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to delete channel {channel_id}: {e}")
        raise e