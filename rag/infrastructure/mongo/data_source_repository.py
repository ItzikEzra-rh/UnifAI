"""MongoDB adapter for DataSourceRepository port."""
import re
from typing import Optional, List, Dict, Any

from pymongo.collection import Collection

from domain.data_source.model import DataSource
from domain.data_source.repository import DataSourceRepository
from shared.logger import logger


class MongoDataSourceRepository(DataSourceRepository):
    """MongoDB implementation of the DataSourceRepository port."""

    def __init__(self, collection: Collection):
        self._col = collection

    def find_by_id(self, source_id: str) -> Optional[DataSource]:
        """Get source by source_id."""
        doc = self._col.find_one({"source_id": source_id})
        return self._to_model(doc) if doc else None

    def find_by_pipeline_id(self, pipeline_id: str) -> Optional[DataSource]:
        """Get source by pipeline_id."""
        doc = self._col.find_one({"pipeline_id": pipeline_id})
        return self._to_model(doc) if doc else None

    def find_all(self, source_type: Optional[str] = None) -> List[DataSource]:
        """Get all sources, optionally filtered by type."""
        query = {"source_type": source_type.upper()} if source_type else {}
        docs = self._col.find(query)
        return [self._to_model(doc) for doc in docs]

    def get_paginated(
            self,
            field_path: Optional[str] = None,
            cursor: Optional[str] = None,
            limit: int = 50,
            search_regex: Optional[str] = None,
            match_filter: Optional[Dict[str, Any]] = None,
            sort_by: Optional[str] = None,
            sort_order: int = -1,
        ) -> Dict[str, Any]:
            """
            Generic paginated query for any field or full documents.
            
            Args:
                field_path: Dot-notation path to field (e.g. "tags", "metadata.category"). 
                            None returns full documents.
                cursor: Pagination cursor (skip count as string)
                limit: Number of items to return
                search_regex: Regex pattern to filter results
                match_filter: Additional match conditions (e.g. {"source_type": "DOCUMENT"})
                sort_by: Field to sort by (defaults to "_id" for fields, "created_at" for docs)
                sort_order: 1 for ascending, -1 for descending
                
            Returns:
                {"data": [...], "nextCursor": str|None, "hasMore": bool, "total": int}
            """
            skip = int(cursor) if cursor and cursor.isdigit() else 0
            pipeline = []
            
            start_anchored = f"^{re.escape(search_regex)}" if search_regex else None
            
            # Base match filter
            if match_filter:
                pipeline.append({"$match": match_filter})
            
            if field_path:
                # DISTINCT VALUES MODE - extract unique values from a field
                pipeline.append({"$unwind": f"${field_path}"})
                
                if start_anchored:
                    pipeline.append({"$match": {field_path: {"$regex": start_anchored, "$options": "i"}}})
                else:
                    pipeline.append({"$match": {field_path: {"$exists": True, "$ne": None, "$ne": ""}}})
                
                pipeline.append({"$group": {"_id": f"${field_path}"}})
                pipeline.append({"$sort": {"_id": sort_order if sort_order else 1}})
            else:
                # FULL DOCUMENTS MODE
                if start_anchored:
                    pipeline.append({"$match": {"source_name": {"$regex": start_anchored, "$options": "i"}}})
                
                sort_field = sort_by or "created_at"
                pipeline.append({"$sort": {sort_field: sort_order}})
            
            # Build data pipeline stages
            data_pipeline = [{"$skip": skip}, {"$limit": limit}]
            
            # Facet for pagination
            pipeline.append({
                "$facet": {
                    "metadata": [{"$count": "total"}],
                    "data": data_pipeline
                }
            })
            
            try:
                result = list(self._col.aggregate(pipeline))
                
                total = 0
                items = []
                
                if result and result[0]:
                    facet = result[0]
                    if facet.get("metadata"):
                        total = facet["metadata"][0]["total"]
                    
                    if field_path:
                        items = [item["_id"] for item in facet.get("data", [])]
                    else:
                        items = facet.get("data", [])
                
                next_cursor = str(skip + len(items)) if (skip + len(items)) < total else None
                
                return {
                    "data": items,
                    "nextCursor": next_cursor,
                    "hasMore": next_cursor is not None,
                    "total": total
                }
            except Exception as e:
                logger.error(f"Error in paginated query (field={field_path}): {e}")
                return {"data": [], "nextCursor": None, "hasMore": False, "total": 0}

    def save(self, source: DataSource) -> None:
        """Insert or update a source (upsert by pipeline_id)."""
        doc = self._to_document(source)
        self._col.update_one(
            {"pipeline_id": source.pipeline_id},
            {
                "$set": doc,
                "$setOnInsert": {"created_at": source.created_at}
            },
            upsert=True,
        )

    def delete(self, source_id: str) -> bool:
        """Delete source by ID. Returns True if deleted."""
        result = self._col.delete_one({"source_id": source_id})
        return result.deleted_count > 0

    # --- Mapping methods ---
    def _to_model(self, doc: Dict[str, Any]) -> DataSource:
        """Convert MongoDB document to domain model."""
        return DataSource.from_dict(doc)

    def _to_document(self, source: DataSource) -> Dict[str, Any]:
        """Convert domain model to MongoDB document."""
        doc = source.to_dict()
        doc.pop("created_at", None)  # Handled separately in upsert
        return doc

