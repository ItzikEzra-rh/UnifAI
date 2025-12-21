"""DataSource repository port (interface)."""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any

from domain.data_source.model import DataSource


class DataSourceRepository(ABC):
    """Port for DataSource persistence - one interface per aggregate."""

    @abstractmethod
    def find_by_id(self, source_id: str) -> Optional[DataSource]:
        """Get source by source_id."""
        ...

    @abstractmethod
    def find_by_pipeline_id(self, pipeline_id: str) -> Optional[DataSource]:
        """Get source by pipeline_id."""
        ...

    @abstractmethod
    def find_all(self, source_type: Optional[str] = None) -> List[DataSource]:
        """Get all sources, optionally filtered by type."""
        ...

    @abstractmethod
    def find_paginated(
        self,
        cursor: Optional[str] = None,
        limit: int = 50,
        source_type: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Paginated query returning {data, next_cursor, has_more, total}."""
        ...

    @abstractmethod
    def save(self, source: DataSource) -> None:
        """Insert or update a source (upsert by pipeline_id)."""
        ...

    @abstractmethod
    def delete(self, source_id: str) -> bool:
        """Delete source by ID. Returns True if deleted."""
        ...

    @abstractmethod
    def get_distinct_values(
        self,
        field: str,
        source_type: Optional[str] = None,
        search: Optional[str] = None,
        cursor: Optional[str] = None,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """
        Get distinct values from a field (e.g., tags, categories).
        
        Args:
            field: Field path to extract distinct values from (e.g., "tags")
            source_type: Filter by source type
            search: Filter values by prefix (case-insensitive)
            cursor: Pagination cursor
            limit: Max values to return
            
        Returns:
            {data: List[str], next_cursor, has_more, total}
        """
        ...

