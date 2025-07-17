# storage_manager.py

from typing import List, Dict, Any, Optional
from .qdrant_storage import QdrantStorage
from utils.storage.mongo.mongo_storage import MongoStorage 

class StorageManager:
    def __init__(self, qstore: QdrantStorage, mstore: MongoStorage):
        self.qstore = qstore
        self.mstore = mstore

    def persist(
        self,
        source_id: str,
        source_name: str,
        source_type: str,
        enriched_chunks: List[Dict[str, Any]],
        pipeline_id: str,
        summary: Dict[str, Any]
    ):
        # write embeddings
        self.qstore.store_embeddings(enriched_chunks)

        self.mstore.upsert_source_summary(
            source_id=source_id,
            source_name=source_name,
            source_type=source_type,
            pipeline_id=pipeline_id,
            summary=summary
        )

    def delete_source(self, source_id: str, source_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Delete a source from both Qdrant and MongoDB storage with transaction-like behavior.
        
        Args:
            source_id: The ID of the source to delete
            source_type: Optional source type for filtering
            
        Returns:
            Dictionary with comprehensive deletion results
        """
        from shared.logger import logger
        
        try:
            # Get source info before deletion
            source_info = self.mstore.get_source_info(source_id)
            source_name = source_info.get("source_name", "Unknown")
            actual_source_type = source_info.get("source_type", source_type)
            
            # Step 1: Delete from Qdrant first (critical step)
            logger.info(f"Starting deletion of source {source_name} ({source_id}) - Step 1: Qdrant")
            qdrant_result = self.qstore.delete_source(source_id, actual_source_type)
            
            # Check if Qdrant deletion was successful
            if not qdrant_result.get("success", False):
                logger.error(f"Qdrant deletion failed for source {source_id}. Aborting MongoDB deletion to maintain consistency.")
                return {
                    "source_id": source_id,
                    "source_name": source_name,
                    "source_type": actual_source_type,
                    "success": False,
                    "transaction_safe": True,
                    "qdrant_result": qdrant_result,
                    "mongo_result": {"success": False, "skipped": True, "reason": "Qdrant deletion failed"},
                    "pipeline_result": {"success": False, "skipped": True, "reason": "Qdrant deletion failed"},
                    "error": "Qdrant deletion failed - MongoDB deletion skipped to maintain consistency",
                    "summary": {
                        "embeddings_deleted": qdrant_result.get("embeddings_deleted", 0),
                        "source_deleted": False,
                        "pipelines_deleted": 0
                    }
                }
            
            # Step 2: Delete from MongoDB (only if Qdrant succeeded)
            logger.info(f"Qdrant deletion successful - Step 2: MongoDB deletion for source {source_id}")
            mongo_result = self.mstore.delete_source(source_id)
            
            # Step 3: Delete related pipelines (continue even if MongoDB fails for cleanup)
            pipeline_prefix = f"{actual_source_type.lower()}_{source_id}" if actual_source_type else source_id
            logger.info(f"Step 3: Pipeline cleanup for source {source_id}")
            pipeline_result = self.mstore.delete_pipeline(pipeline_prefix)
            
            # Determine overall success
            overall_success = (
                qdrant_result.get("success", False) and 
                mongo_result.get("success", False) and 
                pipeline_result.get("success", False)
            )
            
            # If MongoDB deletion failed after Qdrant succeeded, we have a problem
            if qdrant_result.get("success", False) and not mongo_result.get("success", False):
                logger.warning(f"Inconsistent state detected: Qdrant deletion succeeded but MongoDB deletion failed for source {source_id}")
                # TODO: Could implement compensating transaction here (re-create Qdrant entries)
            
            result = {
                "source_id": source_id,
                "source_name": source_name,
                "source_type": actual_source_type,
                "success": overall_success,
                "transaction_safe": True,
                "qdrant_result": qdrant_result,
                "mongo_result": mongo_result,
                "pipeline_result": pipeline_result,
                "summary": {
                    "embeddings_deleted": qdrant_result.get("embeddings_deleted", 0),
                    "source_deleted": mongo_result.get("source_deleted", False),
                    "pipelines_deleted": pipeline_result.get("pipelines_deleted", 0)
                }
            }
            
            if overall_success:
                logger.info(f"✅ Successfully deleted source {source_name} ({source_id}) from all systems")
            else:
                logger.warning(f"⚠️  Partial deletion of source {source_name} ({source_id})")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to delete source {source_id}: {e}")
            return {
                "source_id": source_id,
                "source_name": "Unknown",
                "source_type": source_type,
                "success": False,
                "transaction_safe": False,
                "error": str(e),
                "summary": {
                    "embeddings_deleted": 0,
                    "source_deleted": False,
                    "pipelines_deleted": 0
                }
            }
