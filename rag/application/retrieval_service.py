"""Retrieval application service - vector search orchestration."""
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

from domain.vector.repository import VectorRepository
from domain.vector.embedder import EmbeddingGenerator
from domain.vector.model import SearchResult
from infrastructure.retrieval.source_filter_resolver import SourceFilterResolver
from shared.logger import logger


@dataclass
class SearchQuery:
    """Value object for search parameters."""
    query_text: str
    source_type: str
    top_k: int = 5
    scope: str = "public"  # "public" or "private"
    user: str = "default"
    doc_ids: Optional[List[str]] = None
    tags: Optional[List[str]] = None


class RetrievalService:
    """
    Application service for vector search/retrieval operations.
    
    Orchestrates:
    - Filter resolution (doc_ids, tags -> source_ids)
    - Query embedding generation
    - Vector search execution
    
    Usage:
        service = retrieval_service("DOCUMENT")  # from app_container
        results = service.search(SearchQuery(
            query_text="How to reset password?",
            source_type="DOCUMENT",
            top_k=5,
            doc_ids=["doc_1"],
        ))
    """
    
    def __init__(
        self,
        embedder: EmbeddingGenerator,
        vector_repo: VectorRepository,
        filter_resolver: SourceFilterResolver,
    ):
        self._embedder = embedder
        self._vector_repo = vector_repo
        self._filter_resolver = filter_resolver
    
    def search(self, query: SearchQuery) -> List[SearchResult]:
        """
        Execute a vector search with optional filtering.
        
        Args:
            query: SearchQuery containing search parameters
            
        Returns:
            List of SearchResult ordered by relevance
        """
        # 1. Resolve source filters (doc_ids/tags -> source_ids)
        allowed_source_ids = self._filter_resolver.resolve(
            source_type=query.source_type,
            doc_ids=query.doc_ids,
            tags=query.tags,
        )
        
        # Early exit if filters applied but no matches
        if allowed_source_ids is not None and not allowed_source_ids:
            logger.info("Filter resolved to empty set - returning no results")
            return []
        
        # 2. Build vector search filters
        filters: Dict[str, Any] = {}
        
        if allowed_source_ids:
            filters["metadata.source_id"] = list(allowed_source_ids)
        
        if query.scope == "private":
            filters["metadata.upload_by"] = query.user
        
        # 3. Generate query embedding
        query_embedding = self._embedder.generate_query_embedding(query.query_text)
        
        # 4. Execute vector search
        results = self._vector_repo.search(
            query_embedding=query_embedding.tolist(),
            top_k=query.top_k,
            filters=filters if filters else None,
        )
        
        logger.info(f"Search returned {len(results)} results for query: {query.query_text[:50]}...")
        return results
    
    def search_simple(
        self,
        query_text: str,
        source_type: str,
        top_k: int = 5,
        scope: str = "public",
        user: str = "default",
    ) -> List[SearchResult]:
        """
        Simple search without doc_id/tag filtering.
        
        Convenience method for basic searches.
        
        Args:
            query_text: The search query
            source_type: Type of source to search (e.g., "DOCUMENT", "SLACK")
            top_k: Number of results to return
            scope: "public" or "private"
            user: User identifier for private scope filtering
            
        Returns:
            List of SearchResult ordered by relevance
        """
        return self.search(SearchQuery(
            query_text=query_text,
            source_type=source_type,
            top_k=top_k,
            scope=scope,
            user=user,
        ))

