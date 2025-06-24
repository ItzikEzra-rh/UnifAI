import time
from utils.storage.mongo_storage import MongoStorage
from utils.storage.storage_manager import StorageManager
from utils.monitor.pipeline_monitor import MongoDBPipelineRepository
import pymongo
import uuid
from flask import session
from data_sources.docs.doc_connector import DocumentConnector
from data_sources.docs.doc_config_manager import DocConfigManager
from data_sources.docs.document_processor import DocumentProcessor
from data_sources.docs.pdf_chunker_strategy import PDFChunkerStrategy
from data_sources.docs.doc_pipeline_scheduler import DocDataPipeline
from utils.embedding.embedding_generator_factory import EmbeddingGeneratorFactory
from utils.storage.vector_storage_factory import VectorStorageFactory
from shared.logger import logger

mongo_client = pymongo.MongoClient("mongodb://ae8f0dd8e6cd046539c3f0b7c6a75f13-508991814.us-east-1.elb.amazonaws.com:27017/")

def get_available_doc_list():
    pipeline_repo = MongoDBPipelineRepository(mongo_client)
    available_docs_query = {"source_type": "DOCUMENT", "status": {"$ne": "FAILED"} }
    docs = pipeline_repo.get_pipeline_by_query(available_docs_query)
    data_source_repo = MongoDBPipelineRepository(mongo_client, database_name="data_sources")
    for doc in docs:
        doc["file_type"] = doc.get("name", "").rsplit(".", 1)[-1].lower()
        pipeline_id = doc["pipeline_id"]
        doc_data = data_source_repo.get_source_by_query({"last_pipeline_id": pipeline_id})
        if not doc_data:
            continue
        doc["chunks"] = doc_data[0].get("chunks_generated", [])
        doc["file_size"] = doc_data[0].get("type_data", {}).get("file_size", 0)
        doc["page_count"] = doc_data[0].get("type_data", {}).get("page_count", 0)
        doc["full_text"] = doc_data[0].get("type_data", {}).get("full_text", "")
    return docs

def embed_docs_flow(doc_list, upload_by):
    config = DocConfigManager()
    config.set_config_value("chunk_size", 800)
    config.set_config_value("chunk_overlap", 100)

    doc_connector = DocumentConnector(config)
    doc_processor = DocumentProcessor()

    # Create PDF chunker
    pdf_chunker = PDFChunkerStrategy(
        max_tokens_per_chunk=config._config["chunk_size"],
        overlap_tokens=config._config["chunk_overlap"]
    )

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
        "url": "http://a467739e076d04bf1b15aa68187cbc05-1112405490.us-east-1.elb.amazonaws.com",
        "port": 6333
    }

    vector_storage = VectorStorageFactory.create(storage_config)
    vector_storage.initialize()

    # Create MongoDB client
    mongo_client = pymongo.MongoClient("mongodb://ae8f0dd8e6cd046539c3f0b7c6a75f13-508991814.us-east-1.elb.amazonaws.com:27017/")
    # Create data pipeline with existing logger
    doc_pipeline = DocDataPipeline(mongo_client, logger=logger)

    qstore = VectorStorageFactory.create(storage_config)
    qstore.initialize()
    manager = StorageManager(qstore, mongo_uri="mongodb://ae8f0dd8e6cd046539c3f0b7c6a75f13-508991814.us-east-1.elb.amazonaws.com:27017")
    response = []
    
    for doc in doc_list:
        try:
            doc_path = doc["doc_path"]
            doc_name = doc["doc_name"]
            doc_id = str(uuid.uuid4())
            start = time.time()
            # Process the slack channel using our pipeline
            doc_pipeline.process_doc(doc_id, doc_name)

            # Start log monitoring - this will uses the event-driven handler system
            doc_pipeline.monitor.start_log_monitoring(target_logger=logger, pipeline_id=f"doc_{doc_id}")

            result = doc_connector.process_document(doc_path, upload_by)
            
            # Process with various options
            processed_documents = doc_processor.process(
                result,
                clean_markdown=False, # Clean markdown content
                clean_text=False,     # Leave text content as is for now
                remove_references=False,  # Don't remove references yet
                preserve_original=True  # Keep original content
            )
            
            embedding_ready_docs = doc_processor.prepare_for_single_doc_embedding(processed_documents)
            
            chunks = pdf_chunker.chunk_content([embedding_ready_docs])
            enriched_chunks = embedding_generator.generate_embeddings(chunks)
            common_summary = {
                "chunks_generated":   len(chunks),
                "embeddings_created": len(enriched_chunks),
                "processing_time_s":  time.time() - start,
                "last_pipeline_id":   f"doc_{doc_id}"
            }

            doc_type_data = {
                "page_count": result.get("metadata", {}).get("page_count", 0),
                "full_text": result.get("text", ""),
                "file_size": result.get("size", "0 MB"),
            }

            manager.persist(
                source_id=doc_id,
                source_name=doc_name,
                upload_by=upload_by,
                source_type="DOCUMENT",
                enriched_chunks=enriched_chunks,
                summary=common_summary,
                type_data=doc_type_data
            )
            
            vector_storage.store_embeddings(enriched_chunks)

            response.append({
                "doc": doc_name,
                "status": "success",
                "chunks_stored": len(enriched_chunks)
            })

            doc_pipeline.monitor.finish_log_monitoring()
        except Exception as e:
            logger.error(f"Failed to embed doc {doc.get('doc_name')}: {str(e)}")
            response.append({
                "doc": doc.get("doc_name"),
                "status": "failed",
                "error": str(e)
            })

    return response

def get_best_match_results(query: str, top_k_results: int = 5, scope: str = "public"):
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
        "url": "http://a467739e076d04bf1b15aa68187cbc05-1112405490.us-east-1.elb.amazonaws.com",
        "port": 6333
    }
    vector_storage = VectorStorageFactory.create(storage_config)
    vector_storage.initialize()
    
    query_embedding = embedding_generator.generate_query_embedding(query)
    
    search_results = vector_storage.search(
        query_embedding=query_embedding,
        top_k=top_k_results,
        filters={"upload_by": session.get('user').get('name', 'default')} if scope == "private" else {}
    )

    return search_results