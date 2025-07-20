import base64
import os
import time
from config.app_config import AppConfig
from utils.storage.mongo.mongo_storage import MongoStorage
from global_utils.utils.util import get_mongo_url
from utils.storage.storage_manager import StorageManager
from utils.monitor.pipeline_monitor import MongoDBPipelineRepository
import pymongo
import uuid
from flask import session, jsonify
from data_sources.docs.doc_connector import DocumentConnector
from data_sources.docs.doc_config_manager import DocConfigManager
from data_sources.docs.document_processor import DocumentProcessor
from data_sources.docs.pdf_chunker_strategy import DoclingProcessingError, PDFChunkerStrategy
from data_sources.docs.doc_pipeline_scheduler import DocDataPipeline
from utils.embedding.embedding_generator_factory import EmbeddingGeneratorFactory
from utils.storage.vector_storage_factory import VectorStorageFactory
from shared.logger import logger
from global_utils.utils.util import get_mongo_url
from utils.storage.mongo.mongo_helpers import get_mongo_storage

app_config = AppConfig()
upload_folder = app_config.get("upload_folder", "")

mongo_client = pymongo.MongoClient(get_mongo_url())
pipeline_repo = MongoDBPipelineRepository(mongo_client)
data_source_repo = MongoStorage(get_mongo_url())

def register_data_sources(data, type, user):
    try:
        # Insert the data queue into the sources db
        for instance in data:
            source_name = instance.get("source_name", "")
            if type == "DOCUMENT":
                doc_path = os.path.join(upload_folder, source_name)
                instance["doc_path"] = doc_path
                instance["source_id"] = str(uuid.uuid4())
            
            start = time.time()
        # return from here the ids there were generated for each one to be used for the pipeline id
    except Exception as e:
        logger.error(f"Failed to register data: {str(e)}")
        return jsonify({"error": str(e)}), 500