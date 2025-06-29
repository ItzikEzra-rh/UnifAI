from flask import current_app
from utils.storage.mongo.mongo_storage import MongoStorage, SourceService 
from global_utils.utils.util import get_mongo_url

mongo_uri = get_mongo_url()

def get_mongo_storage() -> MongoStorage:
    try:
        return current_app.mongo_storage
    except RuntimeError:
        return MongoStorage(mongo_uri)


def get_source_service() -> SourceService:
    try:
        return current_app.source_service
    except RuntimeError:
        store = MongoStorage(mongo_uri)
        return SourceService(store, store)
