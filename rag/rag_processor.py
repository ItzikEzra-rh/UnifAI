from chunking.text_chunker import TextChunker
from embeddings.embeddings_generator import EmbeddingsGenerator
from db.vector_db import VectorDB, DBConfig
from handlers.file_handler import FileHandler 
from typing import Any, Dict

class RAGProcessor:
    def __init__(self,
                 chunker: TextChunker,
                 embeddings_generator: EmbeddingsGenerator,
                 vector_db: VectorDB):
        self.chunker = chunker
        self.embeddings_generator = embeddings_generator
        self.vector_db = vector_db

    def process_file(self, file_path: str, metadata: Dict[str, Any] = None):
        """Process a single file through the RAG pipeline"""
        # Initialize file handler
        file_handler = FileHandler(file_path)
        
        # Generate chunks
        chunks = self.chunker.chunk_file(file_handler)
        
        # Generate embeddings
        embeddings = self.embeddings_generator.generate_embeddings(chunks)
        
        # Store in vector DB
        self.vector_db.store_embeddings(
            file_handler=file_handler,
            chunks=chunks,
            embeddings=embeddings,
            metadata=metadata
        )
        
        # Update FAISS index
        self.vector_db.build_faiss_index()