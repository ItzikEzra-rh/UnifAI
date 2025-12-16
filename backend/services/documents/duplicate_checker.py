from typing import Any, Dict, List, Optional

from config.constants import DataSource, PipelineStatus
from global_utils.utils import compute_file_md5


# Statuses that should block duplicate uploads (successfully processed documents)
BLOCKING_STATUSES = {PipelineStatus.DONE.value}


class DocumentDuplicateChecker:
    """
    Domain service for detecting duplicate documents by content hash (MD5).

    This service depends on a storage facade that exposes `get_source_by_query`.
    It keeps persistence concerns out of validators and orchestrators.
    
    A document is only considered a duplicate if an existing document with the 
    same MD5 hash has been successfully processed (status = DONE). Documents 
    with FAILED or other non-complete statuses are not considered duplicates,
    allowing users to retry failed uploads.
    """

    def __init__(self, storage: Any):
        self._storage = storage

    def _get_pipeline_status(self, pipeline_id: str) -> Optional[str]:
        """Get the status of a pipeline by its ID."""
        if not pipeline_id:
            return None
        
        if not hasattr(self._storage, "get_pipeline_stats"):
            return None
            
        try:
            stats = self._storage.get_pipeline_stats([pipeline_id])
            if stats and pipeline_id in stats:
                return stats[pipeline_id].get("status")
        except Exception:
            pass
        return None

    def find_existing_by_md5(
        self,
        md5: str,
        *,
        source_type: str = DataSource.DOCUMENT.upper_name,
        extra_filters: Optional[Dict[str, Any]] = None,
        only_blocking: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Find existing documents with the same MD5 hash.
        
        Args:
            md5: The MD5 hash to search for
            source_type: The type of source to filter by
            extra_filters: Additional query filters
            only_blocking: If True, only return documents that would block 
                          a new upload (i.e., those with DONE status)
        
        Returns:
            List of matching source documents
        """
        if not hasattr(self._storage, "get_source_by_query"):
            return []

        query: Dict[str, Any] = {
            "source_type": source_type,
            "type_data.md5": md5,
        }
        if extra_filters:
            query.update(extra_filters)

        try:
            result = self._storage.get_source_by_query(query)
            sources = result if isinstance(result, list) else []
            
            if not only_blocking or not sources:
                return sources
            
            # Filter to only include sources with blocking status (DONE)
            blocking_sources = []
            for source in sources:
                pipeline_id = source.get("pipeline_id")
                status = self._get_pipeline_status(pipeline_id)
                if status in BLOCKING_STATUSES:
                    blocking_sources.append(source)
            
            return blocking_sources
        except Exception:
            return []

    def is_duplicate(
        self,
        doc: Dict[str, Any],
        *,
        source_type: str = DataSource.DOCUMENT.upper_name,
        extra_filters: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Determine if the provided document is a duplicate by MD5.

        A document is only considered a duplicate if there's an existing 
        document with the same MD5 hash that has been successfully processed 
        (status = DONE). Failed uploads do not block re-uploads.

        Accepts a doc dict and will attempt to compute or read the MD5 from:
        - doc["md5"]
        - doc["type_data.md5"]
        - compute from doc["doc_path"] or doc["path"] if present
        """
        md5_hash: Optional[str] = None
        if isinstance(doc, dict):
            md5_hash = doc.get("md5") or doc.get("type_data.md5")
            if not md5_hash:
                doc_path = doc.get("doc_path") or doc.get("path")
                if isinstance(doc_path, str):
                    try:
                        md5_hash = compute_file_md5(doc_path)
                    except Exception:
                        md5_hash = None

        if not md5_hash:
            return False

        # Only consider documents with DONE status as blocking duplicates
        existing = self.find_existing_by_md5(
            md5_hash, 
            source_type=source_type, 
            extra_filters=extra_filters,
            only_blocking=True
        )
        return len(existing) > 0


