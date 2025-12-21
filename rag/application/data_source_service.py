"""DataSource application service - CRUD and business logic."""
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, List, Dict, Any

from domain.data_source.model import DataSource
from domain.data_source.repository import DataSourceRepository
from domain.pipeline.repository import PipelineRepository
from domain.vector.repository import VectorRepository


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
        vector_repo: VectorRepository,
    ):
        self._source_repo = source_repo
        self._pipeline_repo = pipeline_repo
        self._vector_repo = vector_repo

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
    ) -> Dict[str, Any]:
        """List sources with pagination."""
        return self._source_repo.find_paginated(cursor, limit, source_type, search)

    def save(self, source: DataSource) -> None:
        """Save (insert or update) a source."""
        self._source_repo.save(source)

    def delete(self, source_id: str) -> DeleteResult:
        """
        Delete a source and all associated data.
        
        Removes:
        - Vector embeddings from Qdrant
        - Pipeline records from MongoDB
        - Source document from MongoDB
        
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

        vectors_deleted = self._vector_repo.delete_by_source_id(source_id)
        pipelines_deleted = self._pipeline_repo.delete(source.pipeline_id)
        source_deleted = self._source_repo.delete(source_id)

        return DeleteResult(
            success=True,
            source_id=source_id,
            source_name=source.source_name,
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

    # --- Business Methods ---
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
        """Get sources enriched with pipeline stats."""
        sources = self._source_repo.find_all(source_type)
        pipeline_ids = [s.pipeline_id for s in sources if s.pipeline_id]
        stats = self._pipeline_repo.get_stats_batch(pipeline_ids)

        result = []
        for source in sources:
            data = asdict(source)
            if source.pipeline_id in stats:
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

        return sorted(result, key=lambda x: x.get("created_at") or 0, reverse=True)

