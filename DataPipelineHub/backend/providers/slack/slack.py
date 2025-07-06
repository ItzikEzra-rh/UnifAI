import time
import pymongo
from data_sources.slack.slack_config_manager import SlackConfigManager
from data_sources.slack.slack_connector import SlackConnector
from data_sources.slack.slack_data_processor import SlackProcessor
from data_sources.slack.slack_chunker_strategy import SlackChunkerStrategy
from data_sources.slack.slack_pipeline_scheduler import SlackDataPipeline
from utils.storage.mongo.mongo_helpers import get_mongo_storage
from utils.storage.storage_manager import StorageManager
from utils.embedding.embedding_generator_factory import EmbeddingGeneratorFactory
from utils.storage.vector_storage_factory import VectorStorageFactory
from shared.logger import logger
from global_utils.utils.util import get_mongo_url

def _get_configured_connector() -> SlackConnector:
    config_manager = SlackConfigManager()
    config_manager.set_project_tokens(
        project_id="example-project",
        bot_token="xoxb-2253118358-8783454711008-dwnxf7cPBpeVLlLw8KMurohb",
        user_token="xoxb-2253118358-8783454711008-dwnxf7cPBpeVLlLw8KMurohb"
    )
    config_manager.set_default_project("example-project")
    return SlackConnector(config_manager)

def get_available_slack_channels(channel_types: str):
    connector = _get_configured_connector()
    if connector.authenticate():
        return connector.get_available_slack_channels(types=channel_types)
    else:
        raise RuntimeError("Slack authentication failed")

def embed_slack_channels_flow(channel_list, upload_by="default"):
    """
    Slack embedding flow function using the SlackEmbeddingService.
    """
    from providers.slack.slack_embedding_service import SlackEmbeddingService, EmbeddingConfig
    
    connector = _get_configured_connector()
    config = EmbeddingConfig()
    
    service = SlackEmbeddingService(
        connector=connector,
        config=config,
        upload_by=upload_by
    )
    
    return service.embed_channels(channel_list)

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
        result = storage_manager.delete_source(channel_id, "SLACK")
        
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