"""DataSource application service - CRUD and business logic."""
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, List, Dict, Any

from typing import Callable

from domain.data_source.model import DataSource
from domain.data_source.repository import DataSourceRepository
from domain.pagination import PaginatedResult
from domain.pipeline.repository import PipelineRepository
from domain.vector.repository import VectorRepository
from shared.logger import logger


@dataclass
class DeleteResult:
    """Result of a source deletion operation."""
    success: bool
    source_id: str = ""
    source_name: str = ""
    source_deleted: bool = False
    pipelines_deleted: int = 0
    vectors_deleted: int = 0
    message: str = ""


class DataSourceService:
    """Application service for DataSource aggregate - CRUD + business logic."""

    def __init__(
        self,
        source_repo: DataSourceRepository,
        pipeline_repo: PipelineRepository,
        vector_repo_factory: Callable[[str], VectorRepository],
    ):
        self._source_repo = source_repo
        self._pipeline_repo = pipeline_repo
        self._vector_repo_factory = vector_repo_factory

    # --- CRUD ---
    def get_by_id(self, source_id: str) -> Optional[DataSource]:
        """Get a source by its source_id."""
        return self._source_repo.find_by_id(source_id)

    def get_by_pipeline_id(self, pipeline_id: str) -> Optional[DataSource]:
        """Get a source by its pipeline_id."""
        return self._source_repo.find_by_pipeline_id(pipeline_id)

    def list_sources(self, source_type: Optional[str] = None) -> List[DataSource]:
        """List all sources, optionally filtered by type."""
        return self._source_repo.find_all(source_type)

    def list_paginated(
        self,
        cursor: Optional[str] = None,
        limit: int = 50,
        source_type: Optional[str] = None,
        search: Optional[str] = None,
    ) -> PaginatedResult[Dict[str, Any]]:
        """List sources with pagination."""
        return self._source_repo.find_paginated(cursor, limit, source_type, search)

    def save(self, source: DataSource) -> None:
        """Save (insert or update) a source."""
        self._source_repo.save(source)

    def delete(self, source_id: str) -> DeleteResult:
        """
        Delete a source and all associated data with transaction-like behavior.
        
        Deletion order (abort on vector failure to maintain consistency):
        1. Vector embeddings from Qdrant (critical - abort if fails)
        2. MongoDB records (pipeline + source document)
        
        Args:
            source_id: The source ID to delete
            
        Returns:
            DeleteResult with deletion details
        """
        source = self._source_repo.find_by_id(source_id)
        if not source:
            return DeleteResult(
                success=False,
                message=f"Source {source_id} not found",
            )

        source_name = source.source_name
        # Get the correct vector repository based on source type
        collection_name = f"{source.source_type.lower()}_data"
        vector_repo = self._vector_repo_factory(collection_name)
        
        try:
            vectors_deleted = vector_repo.delete_by_source_id(source_id)
        except Exception as e:
            return DeleteResult(
                success=False,
                source_id=source_id,
                source_name=source_name,
                message=f"Vector storage deletion failed: {e}",
            )
        try:
            pipelines_deleted = self._pipeline_repo.delete(source.pipeline_id)
            source_deleted = self._source_repo.delete(source_id)
        except Exception as e:
            return DeleteResult(
                success=False,
                source_id=source_id,
                source_name=source_name,
                source_deleted=False,
                pipelines_deleted=0,
                vectors_deleted=vectors_deleted,
                message=f"Partial deletion - MongoDB deletion failed: {e}",
            )
        return DeleteResult(
            success=True,
            source_id=source_id,
            source_name=source_name,
            source_deleted=source_deleted,
            pipelines_deleted=pipelines_deleted,
            vectors_deleted=vectors_deleted,
        )

    def update(self, source_id: str, updates: Dict[str, Any]) -> bool:
        """Update specific fields of a source."""
        source = self._source_repo.find_by_id(source_id)
        if not source:
            return False
        # Apply updates to domain model
        for key, value in updates.items():
            if hasattr(source, key):
                setattr(source, key, value)
        self._source_repo.save(source)
        return True

    # ══════════════════════════════════════════════════════════════════════════
    # Private Helpers
    # ══════════════════════════════════════════════════════════════════════════

    def _enrich_with_pipeline_stats(self, sources: List[DataSource]) -> List[Dict[str, Any]]:
        """
        Enrich sources with pipeline stats.
        
        Single source of truth for stats enrichment logic.
        Batch-optimized: makes one DB call regardless of source count.
        
        Args:
            sources: List of DataSource domain models
            
        Returns:
            List of dicts with source data + status + pipeline_stats
        """
        if not sources:
            return []
        
        # Batch fetch stats for all sources in one query
        pipeline_ids = [s.pipeline_id for s in sources if s.pipeline_id]
        stats = self._pipeline_repo.get_stats_batch(pipeline_ids) if pipeline_ids else {}

        result = []
        for source in sources:
            data = asdict(source)
            if source.pipeline_id and source.pipeline_id in stats:
                record = stats[source.pipeline_id]
                data["status"] = record.status.value
                data["pipeline_stats"] = {
                    "status": record.status.value,
                    **asdict(record.stats),
                }
            else:
                data["status"] = None
                data["pipeline_stats"] = None
            result.append(data)
        
        return result

    # ══════════════════════════════════════════════════════════════════════════
    # Business Methods
    # ══════════════════════════════════════════════════════════════════════════

    def upsert_after_pipeline(
        self,
        source_id: str,
        source_name: str,
        source_type: str,
        pipeline_id: str,
        summary: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Upsert source after pipeline execution completes.
        
        Creates the source if it doesn't exist, or updates sync time and type_data.
        Called by the pipeline executor after successful/failed pipeline run.
        
        Args:
            source_id: Unique source identifier
            source_name: Human-readable source name
            source_type: Type of source (SLACK, DOCUMENT, etc.)
            pipeline_id: Associated pipeline ID
            summary: Optional dict to merge into type_data (e.g. stats, error info)
        """
        existing = self._source_repo.find_by_pipeline_id(pipeline_id)
        now = datetime.utcnow()

        if existing:
            # Update existing source
            existing.last_sync_at = now
            if summary:
                existing.type_data = {**existing.type_data, **summary}
            self._source_repo.save(existing)
        else:
            # Create new source
            source = DataSource(
                source_id=source_id,
                source_name=source_name,
                source_type=source_type,
                pipeline_id=pipeline_id,
                upload_by="",  # Could be passed as param if needed
                created_at=now,
                last_sync_at=now,
                type_data=summary or {},
            )
            self._source_repo.save(source)

    def list_with_stats(self, source_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all sources enriched with pipeline stats."""
        sources = self._source_repo.find_all(source_type)
        result = self._enrich_with_pipeline_stats(sources)
        return sorted(result, key=lambda x: x.get("created_at") or 0, reverse=True)

    def get_with_stats(self, source_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a single source by ID, enriched with pipeline stats.
        
        Used for lazy loading expanded row data in UI.
        
        Args:
            source_id: The source ID to retrieve
            
        Returns:
            Dict with source data + pipeline stats, or None if not found
        """
        source = self._source_repo.find_by_id(source_id)
        if not source:
            return None
        
        enriched = self._enrich_with_pipeline_stats([source])
        return enriched[0]

    # ══════════════════════════════════════════════════════════════════════════
    # Paginated Query Methods (for dropdowns/selectors)
    # ══════════════════════════════════════════════════════════════════════════

    def list_available_docs(
        self,
        cursor: Optional[str] = None,
        limit: int = 50,
        search: Optional[str] = None,
    ) -> PaginatedResult[Dict[str, Any]]:
        """
        Get paginated list of DONE documents for dropdown selection.
        
        Filters to only successfully processed (DONE) documents and
        normalizes the response format for UI consumption.
        
        Args:
            cursor: Pagination cursor
            limit: Max items to return
            search: Filter by name prefix
            
        Returns:
            PaginatedResult with normalized docs {id, name, upload_by}
        """
        # Get paginated sources
        result = self._source_repo.find_paginated(
            cursor=cursor,
            limit=limit,
            source_type="DOCUMENT",
            search=search,
        )
        
        # Convert to domain models for enrichment
        sources = [DataSource.from_dict(d) for d in result.data]
        enriched = self._enrich_with_pipeline_stats(sources)
        
        # Filter to DONE only and normalize
        done_docs = [
            {"id": s["source_id"], "name": s["source_name"], "upload_by": s["upload_by"]}
            for s in enriched
            if s.get("status") == "DONE"
        ]
        
        return PaginatedResult(
            data=done_docs,
            next_cursor=result.next_cursor,
            has_more=result.has_more,
            total=len(done_docs),  # Approximate due to post-filtering
        )

    def get_available_tags(
        self,
        cursor: Optional[str] = None,
        limit: int = 50,
        search: Optional[str] = None,
    ) -> PaginatedResult[Dict[str, str]]:
        """
        Get tags from DONE documents only (for UI dropdowns).
        
        Unlike get_distinct_tags(), this filters to only include tags
        from successfully processed documents.
        
        Args:
            cursor: Pagination cursor
            limit: Max tags to return
            search: Filter tags by prefix (case-insensitive)
            
        Returns:
            PaginatedResult with tag options [{label, value}]
        """
        # Get all DONE sources
        all_sources = self._source_repo.find_all(source_type="DOCUMENT")
        enriched = self._enrich_with_pipeline_stats(all_sources)
        done_sources = [s for s in enriched if s.get("status") == "DONE"]
        
        # Extract unique tags from DONE sources
        all_tags = set()
        for s in done_sources:
            all_tags.update(s.get("tags", []))
        
        # Apply search filter (case-insensitive prefix match)
        if search:
            search_lower = search.lower()
            all_tags = {t for t in all_tags if t.lower().startswith(search_lower)}
        
        # Sort alphabetically and paginate
        sorted_tags = sorted(all_tags)
        skip = int(cursor) if cursor and cursor.isdigit() else 0
        page = sorted_tags[skip:skip + limit]
        
        next_cursor = str(skip + len(page)) if skip + len(page) < len(sorted_tags) else None
        
        return PaginatedResult(
            data=[{"label": t, "value": t} for t in page],
            next_cursor=next_cursor,
            has_more=next_cursor is not None,
            total=len(sorted_tags),
        )

    def get_distinct_tags(
        self,
        cursor: Optional[str] = None,
        limit: int = 50,
        search: Optional[str] = None,
        source_type: Optional[str] = None,
    ) -> PaginatedResult[Dict[str, str]]:
        """
        Get paginated distinct tags for dropdown selection.
        
        Args:
            cursor: Pagination cursor
            limit: Max tags to return
            search: Filter tags by prefix
            source_type: Optional filter by source type
            
        Returns:
            PaginatedResult with tag options [{label, value}]
        """
        result = self._source_repo.get_distinct_values(
            field="tags",
            source_type=source_type,
            search=search,
            cursor=cursor,
            limit=limit,
        )
        
        # Transform to label/value format for dropdowns
        return result.map(lambda tag: {"label": tag, "value": tag})

