import os
import uuid
from datetime import datetime
from config.app_config import AppConfig
from utils.storage.mongo.mongo_storage import MongoStorage
from global_utils.utils.util import get_mongo_url
from shared.logger import logger

app_config = AppConfig()
upload_folder = app_config.get("upload_folder", "")

data_source_repo = MongoStorage(get_mongo_url())

def register_data_sources(data, type, user):
    """
    Register data sources in the sources collection with minimal information.
    
    Args:
        data: List of data sources to register
        type: Type of data source (SLACK or DOCUMENT)
        user: User registering the sources
        
    Returns:
        List of registered sources with their generated source_ids added.
    """
    try:
        registered_sources = []
        
        for instance in data:
            if type == "DOCUMENT":
                source_id = str(uuid.uuid4())
                source_name = instance.get("source_name", "")
                doc_path = os.path.join(upload_folder, source_name)
                instance["doc_path"] = doc_path
            elif type == "SLACK":
                source_id = instance.get("channel_id", "")
                source_name = instance.get("channel_name", "")

            # Create basic source document
            source_document = {
                "source_id": source_id,
                "source_name": source_name,
                "upload_by": user,
                "source_type": type.upper(),
                "created_at": datetime.now()
            }
            
            # Store in sources collection
            data_source_repo.upsert_documents(
                db_name="data_sources",
                col_name="sources", 
                docs=[source_document],
                key_field="source_id"
            )
            
            instance["source_id"] = source_id
            registered_sources.append(instance)
        
        logger.info(f"Successfully registered {len(registered_sources)} {type} sources for user {user}")
        return registered_sources
        
    except Exception as e:
        logger.error(f"Failed to register data sources: {str(e)}")
        raise e