from datetime import datetime
from typing import Any, Dict, Optional
from pymongo import MongoClient
from pymongo.collection import Collection
from config.constants import PipelineStatus
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
        pipeline_id: str,
        source_type: str,
        source_id: str,
        source_name: str,
    ):
        self.pipeline_id = pipeline_id
        self.source_type = source_type
        self.source_id = source_id
        self.source_name = source_name
        mongo_client = MongoClient(get_mongo_url())

        self.pipelines_collection: Collection = mongo_client["pipeline_monitoring"]["pipelines"]
        self.sources_collection: Collection = mongo_client["data_sources"]["sources"]

        # ensure an index on pipeline_id for fast lookups & uniqueness
        self.pipelines_collection.create_index("pipeline_id", unique=True)
        self.sources_collection.create_index("source_id", unique=True)

    def get_pipeline(
        self,
        pipeline_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch the pipeline document with the given pipeline_id.
        Returns None if not found.
        """
        return self.pipelines_collection.find_one({"pipeline_id": pipeline_id})

    def register_pipeline(
        self,
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
        result = self.pipelines_collection.update_one(
            {"pipeline_id": self.pipeline_id},
            {
                "$setOnInsert": {
                    "pipeline_id": self.pipeline_id,
                    "source_type": self.source_type,
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

        existing = self.pipelines_collection.find_one(
            {"pipeline_id": self.pipeline_id},
            {"_id": True}
        )
        return str(existing["_id"])

    def register_data_source(
        self,
        summary: Dict[str, Any] = {}
    ) -> None:
        """
        Register or update a data source in the sources collection.
        Equivalent to upsert_source_summary for data_sources.sources.
        """
        now = datetime.now()
        update_fields = {
            'last_sync_at': now,
        }
        
        # Add each key from summary to type_data using dot notation
        # This preserves existing keys while adding/updating specific ones
        for key, value in summary.items():
            update_fields[f'type_data.{key}'] = value
        insert_fields = {
            'source_id': self.source_id,
            'source_name': self.source_name,
            'source_type': self.source_type,
            'pipeline_id': self.pipeline_id,
            'created_at': now,
        }

        self.sources_collection.update_one(
            {'pipeline_id': self.pipeline_id},
            {
                '$set': update_fields,
                '$setOnInsert': insert_fields
            },
            upsert=True
        )
        
    def _calculate_processing_time(
        self,
        pipeline: Dict[str, Any]
    ) -> float:
        """
        Calculate the total processing time for a pipeline.
        
        Args:
            pipeline: The pipeline document from MongoDB
            
        Returns:
            Processing time in seconds as a float
        """
        now = datetime.now()
        created_at = pipeline.get("created_at", now)
        
        # Handle both datetime objects and string representations
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        
        processing_time = (now - created_at).total_seconds()
        return processing_time
        
    def update_pipeline_status(
        self,
        new_status: str
    ) -> bool:
        """
        Update the 'status' and 'updated_at' fields of the pipeline.
        If status is DONE, also calculate and update the total processing time.
        Returns True if a document was modified.
        """
        now = datetime.now()
        update_fields = {
            "status": new_status,
            "last_updated": now,
        }
        
        # If the pipeline is done, calculate the total processing time
        if new_status == PipelineStatus.DONE.value:
            pipeline = self.get_pipeline(self.pipeline_id)
            if pipeline:
                processing_time = self._calculate_processing_time(pipeline)
                update_fields["stats.processing_time"] = processing_time
        
        result = self.pipelines_collection.update_one(
            {"pipeline_id": self.pipeline_id},
            {"$set": update_fields}
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
        doc = self.pipelines_collection.find_one(
            {"pipeline_id": pipeline_id},
            {field_name: True, "_id": False}
        )
        if not doc:
            return default
        return doc.get(field_name, default)

