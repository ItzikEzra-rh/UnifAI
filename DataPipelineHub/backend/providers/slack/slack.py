from data_sources.slack.slack_config_manager import SlackConfigManager
from data_sources.slack.slack_connector import SlackConnector
from config.constants import DataSource
from utils.storage.mongo.mongo_helpers import get_mongo_storage
from utils.embedding.embedding_generator_factory import EmbeddingGeneratorFactory
from utils.storage.vector_storage_factory import VectorStorageFactory
from shared.logger import logger
from utils.storage.qdrant_storage import QdrantStorage
from utils.storage.storage_deletion_manager import SourceDeletionManager

def _get_configured_connector() -> SlackConnector:
    config_manager = SlackConfigManager()
    config_manager.set_project_tokens(
        project_id="example-project",
        bot_token="xoxb-2253118358-8783454711008-dwnxf7cPBpeVLlLw8KMurohb",
        user_token="xoxb-2253118358-8783454711008-dwnxf7cPBpeVLlLw8KMurohb"
    )
    config_manager.set_default_project("example-project")
    return SlackConnector(config_manager)

def _initialize_embedding_generator():
    """
    Initialize and return the embedding generator.
    
    Returns:
        EmbeddingGenerator: Configured embedding generator instance
    """
    embedding_config = {
        "type": "sentence_transformer",
        "model_name": "all-MiniLM-L6-v2",
        "batch_size": 32
    }
    return EmbeddingGeneratorFactory.create(embedding_config)

def _initialize_vector_storage(embedding_dim: int = 384):
    """
    Initialize and return the vector storage.
    
    Args:
        embedding_dim: Dimension of the embeddings (default: 384)
        
    Returns:
        VectorStorage: Configured and initialized vector storage instance
    """
    storage_config = {
        "type": "qdrant",
        "collection_name": "slack_data",
        "embedding_dim": embedding_dim
        # URL and port will come from app_config via VectorStorageFactory
    }
    vector_storage = VectorStorageFactory.create(storage_config)
    vector_storage.initialize()
    return vector_storage

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

def count_channel_chunks(channel_name: str) -> int:
    vector_storage = _initialize_vector_storage()
    return vector_storage.count(filters={"metadata.channel_name": channel_name})

def get_best_match_results(query: str, top_k_results: int = 5, scope: str = "public", logged_in_user: str = "default"):
    embedding_generator = _initialize_embedding_generator()
    vector_storage = _initialize_vector_storage(embedding_generator.embedding_dim)
    
    query_embedding = embedding_generator.generate_query_embedding(query)
    
    search_results = vector_storage.search(
        query_embedding=query_embedding,
        top_k=top_k_results,
        filters={"upload_by": logged_in_user} if scope == "private" else {}
    )
    return search_results

def _initialize_storage_manager():
    """Initialize and return storage manager for operations."""
    embedding_generator = _initialize_embedding_generator()
    vector_storage = _initialize_vector_storage(embedding_generator.embedding_dim)
    
    mongo_storage = get_mongo_storage()
    vector_store = vector_storage if isinstance(vector_storage, QdrantStorage) else None
    if not vector_store:
        raise RuntimeError("Expected QdrantStorage instance")
    
    return SourceDeletionManager(vector_store, mongo_storage)

def delete_slack_channel(channel_id: str) -> dict:
    """
    Delete a slack channel from both MongoDB and Qdrant storage.
    """
    try:
        storage_manager = _initialize_storage_manager()
        result = storage_manager.delete_source(channel_id, DataSource.SLACK.upper_name)
        
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