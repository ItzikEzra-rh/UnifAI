import base64
import os
from config.app_config import AppConfig
from utils.storage.mongo.mongo_storage import MongoStorage
from global_utils.utils.util import get_mongo_url
from utils.monitor.pipeline_monitor import MongoDBPipelineRepository
import pymongo
from flask import jsonify
from utils.embedding.embedding_generator_factory import EmbeddingGeneratorFactory
from utils.storage.vector_storage_factory import VectorStorageFactory
from shared.logger import logger
from global_utils.utils.util import get_mongo_url
from werkzeug.utils import secure_filename

app_config = AppConfig()
upload_folder = app_config.get("upload_folder", "")

mongo_client = pymongo.MongoClient(get_mongo_url())
pipeline_repo = MongoDBPipelineRepository(mongo_client)
data_source_repo = MongoStorage(get_mongo_url())

def upload_docs(files):
    try:
        for file in files:
            filename = secure_filename(file["name"])
            content = base64.b64decode(file["content"])
            with open(os.path.join(upload_folder, filename), "wb") as f:
                f.write(content)
    except Exception as e:
        logger.error(f"Failed to upload files: {str(e)}")
        return jsonify({"error": str(e)}), 500

def get_best_match_results(query: str, top_k_results: int = 5, scope: str = "public", logged_in_user: str = "default"):
    # Create embedding generator
    embedding_config = {
        "type": "sentence_transformer",
        "model_name": "all-MiniLM-L6-v2",
        "batch_size": 32
    }
    embedding_generator = EmbeddingGeneratorFactory.create(embedding_config)
    
    # Create vector storage
    storage_config = {
        "type": "qdrant",
        "collection_name": "pdf_doc_data",
        "embedding_dim": embedding_generator.embedding_dim,
    }
    vector_storage = VectorStorageFactory.create(storage_config)
    vector_storage.initialize()
    
    query_embedding = embedding_generator.generate_query_embedding(query)
    
    search_results = vector_storage.search(
        query_embedding=query_embedding,
        top_k=top_k_results,
        filters={"upload_by": logged_in_user} if scope == "private" else {}
    )

    return search_results
