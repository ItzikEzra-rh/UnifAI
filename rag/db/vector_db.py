from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from handlers.file_handler import FileHandler
import psycopg2
import numpy as np
import faiss
import json

@dataclass
class DBConfig:
    dbname: str
    user: str
    password: str
    host: str
    port: int

class VectorDB:
    def __init__(self, config: DBConfig):
        self.config = config
        self.index: Optional[faiss.Index] = None

    def initialize_db(self):
        """Initialize database and create necessary tables"""
        conn = self._get_connection()
        cur = conn.cursor()
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id SERIAL PRIMARY KEY,
                file_path TEXT,
                chunk_index INTEGER,
                chunk_text TEXT,
                embedding FLOAT8[],
                metadata JSONB
            )
        """)
        
        conn.commit()
        cur.close()
        conn.close()

    def store_embeddings(self, 
                        file_handler: FileHandler,
                        chunks: List[str],
                        embeddings: List[np.ndarray],
                        metadata: Dict[str, Any] = None):
        """Store embeddings and related data in the database"""
        conn = self._get_connection()
        cur = conn.cursor()
        
        for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            # Replace null characters with a space
            chunk_text = chunk.replace('\0', ' ')
            
            # Convert metadata to JSON string
            metadata_json = json.dumps(metadata) if metadata else 'null'
            
            cur.execute("""
                INSERT INTO documents 
                (file_path, chunk_index, chunk_text, embedding, metadata)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                file_handler.metadata.file_path,
                idx,
                chunk_text,
                embedding.tolist(),
                metadata_json
            ))
        
        conn.commit()
        cur.close()
        conn.close()

    """ 
    FAISS (Facebook AI Similarity Search) uses sophisticated data structures (like inverted file indexes and product quantization) to create a searchable index.
    Speed: FAISS indexing can make similarity search 100-1000x faster than naive approaches
    Scalability: Without indexing, search time grows linearly with the number of embeddings
    Memory Efficiency: FAISS can compress vectors while maintaining search quality
    Approximate Search: Allows trading off a small amount of accuracy for massive speed gains
    """
    def build_faiss_index(self):
        """
        1. Retrieves all embeddings from PostgreSQL
        2. Creates a FAISS index with the same dimensionality as embeddings
        3. Adds embeddings to the index using efficient data structures
        """
        conn = self._get_connection()
        cur = conn.cursor()
        
        # Get all embeddings from database
        cur.execute("SELECT embedding FROM documents")
        embeddings = [np.array(row[0]) for row in cur.fetchall()]
        
        if embeddings:
            # Create index with same dimensions as embeddings
            dimension = len(embeddings[0])  # e.g., 384 for MiniLM
            
            # IndexFlatL2 is the simplest index type that uses L2 (Euclidean) distance
            self.index = faiss.IndexFlatL2(dimension)
            
            # Convert to numpy array and ensure float32 type
            embeddings_array = np.array(embeddings).astype('float32')
            
            # Add vectors to index
            self.index.add(embeddings_array)
            
        cur.close()
        conn.close()

    def _get_connection(self):
        return psycopg2.connect(
            dbname=self.config.dbname,
            user=self.config.user,
            password=self.config.password,
            host=self.config.host,
            port=self.config.port
        )