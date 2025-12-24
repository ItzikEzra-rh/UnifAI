"""
RAG Application Container - Composition root with singleton instances via lru_cache.

Each function creates a singleton instance on first call, then returns the cached
instance on subsequent calls. Dependencies are wired here, not scattered across
the codebase.

Usage:
    from bootstrap.app_container import pipeline_service, monitoring_service
    
    # Services are singleton - same instance returned on every call
    svc = pipeline_service()
    svc.register(pipeline_id, source_type)
"""

from functools import lru_cache
from pymongo import MongoClient

from global_utils.utils.util import get_mongo_url


# ══════════════════════════════════════════════════════════════════════════════
# INFRASTRUCTURE - Shared resources
# ══════════════════════════════════════════════════════════════════════════════

@lru_cache(maxsize=1)
def mongo_client() -> MongoClient:
    """Shared MongoDB client (connection pool)."""
    return MongoClient(get_mongo_url())


@lru_cache(maxsize=1)
def pipeline_monitoring_db():
    """Database for pipeline monitoring."""
    return mongo_client()["pipeline_monitoring"]


@lru_cache(maxsize=1)
def data_sources_db():
    """Database for data sources."""
    return mongo_client()["data_sources"]


# ══════════════════════════════════════════════════════════════════════════════
# REPOSITORIES (Infrastructure adapters implementing domain ports)
# ══════════════════════════════════════════════════════════════════════════════

@lru_cache(maxsize=1)
def pipeline_repository():
    """Pipeline repository (Mongo adapter)."""
    from infrastructure.mongo.pipeline_repository import MongoPipelineRepository
    return MongoPipelineRepository(pipeline_monitoring_db()["pipelines"])


@lru_cache(maxsize=1)
def data_source_repository():
    """Data source repository (Mongo adapter)."""
    from infrastructure.mongo.data_source_repository import MongoDataSourceRepository
    return MongoDataSourceRepository(data_sources_db()["sources"])


@lru_cache(maxsize=1)
def monitoring_repository():
    """Monitoring repository (Mongo adapter)."""
    from infrastructure.mongo.monitoring_repository import MongoMonitoringRepository
    return MongoMonitoringRepository(pipeline_monitoring_db())


@lru_cache(maxsize=None)
def vector_repository(collection_name: str):
    from bootstrap.factories import VectorRepositoryFactory    
    return VectorRepositoryFactory.create({
        "type": "qdrant",
        "collection_name": collection_name,
        "embedding_dim": embedding_generator().embedding_dim,
    }).initialize()


# ══════════════════════════════════════════════════════════════════════════════
# PROCESSORS (Domain layer - stateless data transformers)
# ══════════════════════════════════════════════════════════════════════════════

@lru_cache(maxsize=1)
def slack_processor():
    """Slack message processor."""
    from domain.processor.slack_processor import SlackProcessor
    return SlackProcessor()


@lru_cache(maxsize=1)
def document_processor():
    """Document (PDF/Markdown) processor."""
    from domain.processor.document_processor import DocumentProcessor
    return DocumentProcessor()


# ══════════════════════════════════════════════════════════════════════════════
# CHUNKERS (Infrastructure layer - content splitting strategies)
# ══════════════════════════════════════════════════════════════════════════════

@lru_cache(maxsize=1)
def slack_chunker():
    """Slack conversation chunker with default settings."""
    from infrastructure.chunking.slack_chunker import SlackChunkerStrategy
    return SlackChunkerStrategy(
        max_tokens_per_chunk=500,
        overlap_tokens=50,
    )


@lru_cache(maxsize=1)
def pdf_chunker():
    """PDF/Document chunker with default settings."""
    from infrastructure.chunking.pdf_chunker import PDFChunkerStrategy
    return PDFChunkerStrategy(
        max_tokens_per_chunk=500,
        overlap_tokens=50,
    )


# ══════════════════════════════════════════════════════════════════════════════
# APPLICATION SERVICES
# ══════════════════════════════════════════════════════════════════════════════

@lru_cache(maxsize=1)
def pipeline_service():
    """Pipeline application service."""
    from application.pipeline_service import PipelineService
    return PipelineService(pipeline_repo=pipeline_repository())


@lru_cache(maxsize=1)
def monitoring_service():
    """Monitoring application service."""
    from application.monitoring_service import MonitoringService
    return MonitoringService(
        monitoring_repo=monitoring_repository(),
        pipeline_repo=pipeline_repository(),
    )


# ══════════════════════════════════════════════════════════════════════════════
# EMBEDDING & VECTOR COMPONENTS
# ══════════════════════════════════════════════════════════════════════════════

@lru_cache(maxsize=1)
def embedding_generator():
    """Shared embedding generator (sentence transformer)."""
    from bootstrap.factories import EmbeddingGeneratorFactory
    return EmbeddingGeneratorFactory.create({"type": "sentence_transformer"})


# ══════════════════════════════════════════════════════════════════════════════
# UTILITY - Cache management for testing
# ══════════════════════════════════════════════════════════════════════════════

def clear_all_caches():
    """
    Clear all singleton caches. Useful for testing.
    
    Usage:
        from bootstrap.app_container import clear_all_caches
        clear_all_caches()  # Fresh instances will be created on next access
    """
    # Infrastructure
    mongo_client.cache_clear()
    pipeline_monitoring_db.cache_clear()
    data_sources_db.cache_clear()
    # Repositories
    pipeline_repository.cache_clear()
    data_source_repository.cache_clear()
    monitoring_repository.cache_clear()
    vector_repository.cache_clear()
    # Processors
    slack_processor.cache_clear()
    document_processor.cache_clear()
    # Chunkers
    slack_chunker.cache_clear()
    pdf_chunker.cache_clear()
    # Services
    pipeline_service.cache_clear()
    monitoring_service.cache_clear()
    # Embedding
    embedding_generator.cache_clear()

