from config.constants import DataSource 
from utils.storage.mongo.mongo_helpers import get_mongo_storage
from shared.logger import logger
from utils.embedding.embedding_generator_factory import EmbeddingGeneratorFactory
from utils.storage.vector_storage_factory import VectorStorageFactory
from utils.storage.qdrant_storage import QdrantStorage
from utils.storage.storage_deletion_manager import SourceDeletionManager

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
    }
    vector_storage = VectorStorageFactory.create(storage_config)
    vector_storage.initialize()
    return vector_storage


def _initialize_storage_manager():
    """Initialize and return storage manager for operations."""
    embedding_generator = _initialize_embedding_generator()
    vector_storage = _initialize_vector_storage(embedding_generator.embedding_dim)
    
    mongo_storage = get_mongo_storage()
    vector_store = vector_storage if isinstance(vector_storage, QdrantStorage) else None
    if not vector_store:
        raise RuntimeError("Expected QdrantStorage instance")
    
    return SourceDeletionManager(vector_store, mongo_storage)

def get_available_data_sources(source_type: str):
    """
    Fetches a list of available data sources of a specific type.
    
    Args:
        source_type: The type of data source (e.g., 'DOCUMENT', 'DATABASE', etc.)
        user: Optional user filter to get sources for a specific user
        
    Returns:
        List of available data sources matching the criteria
    """
    try:
        svc = get_mongo_storage()
        source_type_upper = source_type.upper()      
        all_sources = svc.list_sources(source_type_upper)       
        return all_sources
        
    except Exception as e:
        logger.error(f"Failed to get available data sources for type {source_type}: {str(e)}")
        return []   

def delete_data_source(pipeline_id: str):
    """
    Delete a data source by its pipeline ID.
    
    Args:
        pipeline_id: The ID of the pipeline/source to delete
        source_type: Optional source type for additional validation/logging
        
    Returns:
        dict: Result of deletion operation with success status and details
    """
    try:
        storage_manager = _initialize_storage_manager()
        result = storage_manager.delete_source(pipeline_id, DataSource.SLACK.upper_name)
        
        summary = result.get("summary", {})
        return {
            "success": result.get("success", False),
            "result": {
                "pipeline_id": result.get("source_id"),
                "source_name": result.get("source_name"),
                "qdrant_embeddings_deleted": summary.get("embeddings_deleted", 0),
                "mongo_source_deleted": summary.get("source_deleted", False),
                "mongo_pipelines_deleted": summary.get("pipelines_deleted", 0)
            }
        }
    except Exception as e:
        logger.error(f"Failed to delete channel {pipeline_id}: {e}")
        raise e

def get_data_source_by_id(pipeline_id: str, source_type: str = None):
    """
    Get a specific data source by its pipeline ID.
    
    Args:
        pipeline_id: The ID of the pipeline/source to retrieve
        source_type: Optional source type for additional filtering
        
    Returns:
        dict: Data source information or None if not found
    """
    try:
        svc = get_mongo_storage()
        source = svc.get_source(pipeline_id)
        
        # Additional type validation if specified
        if source and source_type:
            if source.get('source_type', '').upper() != source_type.upper():
                logger.warning(f"Source type mismatch for {pipeline_id}. Expected: {source_type}, Found: {source.get('source_type')}")
                return None
                
        return source
        
    except Exception as e:
        logger.error(f"Failed to get data source {pipeline_id}: {str(e)}")
        return None
