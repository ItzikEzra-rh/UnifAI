from typing import List, Dict, Any
from .qdrant_storage import QdrantStorage
from utils.storage.mongo_storage import MongoStorage

class StorageManager:
    def __init__(self, qstore: QdrantStorage, mongo_uri: str):
        self.qstore = qstore
        self.mstore = MongoStorage(mongo_uri)

    def persist(
        self,
        source_id: str,
        source_name: str,
        source_type: str,
        enriched_chunks: List[Dict[str, Any]],
        summary: Dict[str, Any],
        type_data: Dict[str, Any]
    ):
        # Delegate Qdrant upsert to your existing, working method
        self.qstore.store_embeddings(enriched_chunks)

        # Upsert the source summary, including type-specific data
        self.mstore.upsert_source_summary(
            source_id=source_id,
            source_name=source_name,
            source_type=source_type,
            summary=summary,
            type_data=type_data
        )