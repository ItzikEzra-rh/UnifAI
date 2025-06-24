from pymongo import MongoClient, UpdateOne
from datetime import datetime
from typing import List, Dict, Any, Optional

class MongoStorage:
    """
    Handles persisting chunk text/metadata and source summaries into MongoDB.
    """
    def __init__(self, mongo_uri: str, db_name: str = "data_sources"):
        self.client = MongoClient(mongo_uri)
        self.db = self.client[db_name]
        self.chunks_col = self.db["chunks"]
        self.sources_col = self.db["sources"]
        # Ensure indexes for fast upserts and queries
        self.chunks_col.create_index([("source_id",1), ("chunk_index",1)], unique=True)
        self.sources_col.create_index("source_id", unique=True)

    def upsert_chunks(self, source_id: str, chunks: List[Dict[str, Any]]):
        """
        Bulk upsert each chunk into the `chunks` collection.
        Each doc uses <source_id>_<chunk_index> as _id to match Qdrant point IDs.
        """
        ops = []
        for idx, chunk in enumerate(chunks):
            doc_id = f"{source_id}_{idx}"
            doc = {
                "_id": doc_id,
                "source_id": source_id,
                "text": chunk["text"],
                **chunk["metadata"]
            }
            ops.append(
                UpdateOne(
                    {"_id": doc_id},
                    {"$set": doc},
                    upsert=True
                )
            )
        if ops:
            self.chunks_col.bulk_write(ops)

    def upsert_source_summary(
        self,
        source_id: str,
        source_name: str,
        source_type: str,
        upload_by: str,
        summary: Dict[str, Any],
        type_data: Optional[Dict[str, Any]] = None
    ):
        now = datetime.utcnow()
        doc: Dict[str, Any] = {
            "source_id":       source_id,
            "source_name":     source_name,
            "source_type":     source_type,
            "upload_by":       upload_by,
            "last_sync_at":    now,
            **summary
        }
        if type_data is not None:
            doc["type_data"] = type_data

        self.sources_col.update_one(
            {"source_id": source_id},
            {"$set": doc, "$setOnInsert": {"created_at": now}},
            upsert=True
        )
     
    def get_all_sources(
        self,
        source_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve all stored sources (channels), optionally filtered by type.
        """
        query: Dict[str, Any] = {}
        if source_type:
            query["source_type"] = source_type.upper()
        cursor = self.sources_col.find(query)
        return list(cursor)