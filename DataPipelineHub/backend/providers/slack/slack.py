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

def get_available_slack_channels(channel_types: str, cursor: str = "", limit: int = 50, search_regex: str = None):
    connector = _get_configured_connector()
    if connector.authenticate():
        return connector.get_available_slack_channels(types=channel_types, cursor=cursor, limit=limit, search_regex=search_regex)
    else:
        raise RuntimeError("Slack authentication failed")

def get_slack_user_info(user_id: str = None, include_locale: bool = False):
    """
    Get user information from Slack using the users.info API.
    
    Args:
        user_id: User ID to get info for. If None, gets info for the current authenticated user.
        include_locale: Whether to include locale information in the response.
        
    Returns:
        Dictionary containing user information from Slack API
        
    Raises:
        RuntimeError: If Slack authentication fails
        Exception: If the API request fails
    """
    connector = _get_configured_connector()
    if connector.authenticate():
        return connector.get_user_info(user_id=user_id, include_locale=include_locale)
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