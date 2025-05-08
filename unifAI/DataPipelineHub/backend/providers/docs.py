from data_sources.docs.doc_connector import DocumentConnector
from data_sources.docs.doc_config_manager import DocConfigManager
from data_sources.docs.document_processor import DocumentProcessor
from data_sources.docs.pdf_chunker_strategy import PDFChunkerStrategy
from utils.embedding.embedding_generator_factory import EmbeddingGeneratorFactory
from utils.storage.vector_storage_factory import VectorStorageFactory
from shared.logger import logger

def get_available_doc_list():
    # TODO: NotImplemented
    # Assuming we have a volume where all the docs which were uploaded by the users reside under
    # Scan the volume, return for each doc his name and location (path) 
    return {
        "doc_name": "",
        "doc_path": ""
    }

def embed_docs_flow(doc_list):
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
        "url": "http://localhost",
        "port": 6333
    }

    vector_storage = VectorStorageFactory.create(storage_config)
    vector_storage.initialize()

    response = []
    for doc in doc_list:
        try:
            doc_path = doc["doc_path"]
            doc_name = doc["doc_name"]
        
            result = doc_connector.process_document(doc_path)
            
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
            vector_storage.store_embeddings(enriched_chunks)

            response.append({
                "doc": doc_name,
                "status": "success",
                "chunks_stored": len(enriched_chunks)
            })

        except Exception as e:
            logger.error(f"Failed to embed doc {doc.get('doc_name')}: {str(e)}")
            response.append({
                "doc": doc.get("doc_name"),
                "status": "failed",
                "error": str(e)
            })

    return response