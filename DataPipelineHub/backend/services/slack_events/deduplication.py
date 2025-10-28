"""
Event de-duplication using MongoDB TTL collection.
"""
from pymongo.errors import DuplicateKeyError
from utils.storage.mongo.mongo_helpers import get_mongo_storage
from config.constants import Database
from shared.logger import logger
import time


def ensure_dedup_collection():
    """
    Ensure the slack_event_dedup collection exists with TTL index.
    
    Creates a TTL index on createdAt field that expires documents after 600 seconds (10 minutes).
    This is called lazily on first event processing.
    """
    mongo_storage = get_mongo_storage()
    db_name = Database.DATA_SOURCES.value
    collection_name = "slack_event_dedup"
    
    # Get collection via the internal connection
    collection = mongo_storage._conn.get_collection(db_name, collection_name)
    
    # Check if TTL index exists
    indexes = collection.list_indexes()
    ttl_index_exists = False
    
    for index in indexes:
        if index.get('name') == 'ttl_createdAt_600':
            ttl_index_exists = True
            break
    
    # Create TTL index if it doesn't exist
    if not ttl_index_exists:
        collection.create_index(
            "createdAt",
            expireAfterSeconds=600,
            name="ttl_createdAt_600"
        )
        logger.info("Created TTL index on slack_event_dedup collection (expireAfterSeconds=600)")
    
    return collection


def is_event_processed(event_id: str) -> bool:
    """
    Check if event has been processed and mark it as processed.
    
    Uses MongoDB TTL collection with _id as the event_id for de-duplication.
    Documents expire after 10 minutes (TTL index).
    
    Args:
        event_id: Unique event ID from Slack
        
    Returns:
        True if event was already processed (duplicate), False if new
    """
    try:
        collection = ensure_dedup_collection()
        
        # Try to insert document with event_id as _id
        doc = {
            "_id": event_id,
            "createdAt": time.time()
        }
        
        collection.insert_one(doc)
        
        # If insert succeeded, this is a new event
        return False
        
    except DuplicateKeyError:
        # Event already exists in dedup collection (duplicate)
        logger.info(f"Event {event_id} already processed (duplicate), skipping")
        return True
    except Exception as e:
        logger.error(f"Error checking event dedup for {event_id}: {e}")
        # On error, assume not processed to avoid missing events
        return False


