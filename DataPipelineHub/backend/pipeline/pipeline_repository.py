from datetime import datetime
from typing import Any, Dict, Optional
from pymongo import MongoClient
from pymongo.collection import Collection
from config.constants import PipelineStatus, SourceType
from global_utils.utils.util import get_mongo_url

class PipelineRepository:
    """
    Repository for pipeline documents in MongoDB.
    Documents have at least:
      - pipeline_id: str
      - source_type: str
      - status: str
      - metadata: dict (optional)
      - created_at: datetime
      - updated_at: datetime
    """

    def __init__(
        self,
        mongo_client: MongoClient = None,
        db_name: str = "pipeline_monitoring",
        col_name: str = "pipelines"
    ):
        if mongo_client is None:
            mongo_client = MongoClient(get_mongo_url())

        self.collection: Collection = mongo_client[db_name][col_name]
        # ensure an index on pipeline_id for fast lookups & uniqueness
        self.collection.create_index("pipeline_id", unique=True)

    def get_pipeline(
        self,
        pipeline_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch the pipeline document with the given pipeline_id.
        Returns None if not found.
        """
        return self.collection.find_one({"pipeline_id": pipeline_id})

    def register_pipeline(
        self,
        pipeline_id: str,
        source_type: SourceType,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a new pipeline doc if one doesn’t exist, or leave the existing one.
        Returns the ObjectId (as str) of the pipeline document.
        """
        now = datetime.now()
        default_stats = {
            "documents_retrieved": 0,
            "chunks_generated":    0,
            "embeddings_created":  0,
            "api_calls":           0,
            "processing_time":     0,
        }
        result = self.collection.update_one(
            {"pipeline_id": pipeline_id},
            {
                "$setOnInsert": {
                    "pipeline_id": pipeline_id,
                    "source_type": source_type,
                    "status":      PipelineStatus.PENDING.value,
                    "created_at":  now,
                    "stats":       default_stats,
                    "metadata":    metadata or {}
                },
                "$set": {
                    "last_updated": now
                }
            },
            upsert=True
        )
        if result.upserted_id:
            return str(result.upserted_id)

        existing = self.collection.find_one(
            {"pipeline_id": pipeline_id},
            {"_id": True}
        )
        return str(existing["_id"])

    def update_pipeline_status(
        self,
        pipeline_id: str,
        new_status: PipelineStatus
    ) -> bool:
        """
        Update only the 'status' and 'updated_at' fields of the pipeline.
        Returns True if a document was modified.
        """
        result = self.collection.update_one(
            {"pipeline_id": pipeline_id},
            {
                "$set": {
                    "status": new_status,
                    "last_updated": datetime.now(),
                }
            }
        )
        return result.modified_count > 0

    def get_pipeline_field(
        self,
        pipeline_id: str,
        field_name: str,
        default: Any = None
    ) -> Any:
        """
        Retrieve a single field from the pipeline document.

        Args:
            pipeline_id: the pipeline's unique ID
            field_name: the document field you want
            default:    what to return if the doc or field isn't found

        Returns:
            The field's value, or `default`.
        """
        doc = self.collection.find_one(
            {"pipeline_id": pipeline_id},
            {field_name: True, "_id": False}
        )
        if not doc:
            return default
        return doc.get(field_name, default)