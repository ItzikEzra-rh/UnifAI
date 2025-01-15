import numpy as np
from typing import List, Tuple
from db.vector_db import VectorDB, DBConfig
from embeddings.embeddings_generator import EmbeddingsGenerator
from chunking.text_chunker import TextChunker  

class RAGRetriever:
    def __init__(self, vector_db: VectorDB):
        self.vector_db = vector_db

    def retrieve_relevant_context(self, query_text: str, k: int = 5) -> List[Tuple[str, float]]:
        """
        Retrieves the most relevant text chunks and their similarity scores based on the query text.
        
        Parameters:
        query_text (str): The user's query text.
        k (int): The number of most relevant chunks to retrieve.
        
        Returns:
        List[Tuple[str, float]]: A list of tuples containing the relevant text chunks and their similarity scores.
        """
        # Generate the query embedding
        query_embedding = EmbeddingsGenerator().generate_embeddings([query_text])[0]
        
        # Use the FAISS index to find the k most similar embeddings
        distances, indices = self.vector_db.index.search(query_embedding.reshape(1, -1), k)
        
        # Retrieve the corresponding text chunks and similarity scores
        relevant_chunks = []
        for i, index in enumerate(indices[0]):
            conn = self.vector_db._get_connection()
            cur = conn.cursor()
            
            # Convert numpy.int64 to regular int
            index = int(index)
            cur.execute("SELECT chunk_text, embedding FROM documents WHERE chunk_index = %s", (index,))
            row = cur.fetchone()
            chunk_text, chunk_embedding = row
            similarity = 1 - distances[0][i]  # Similarity is 1 - distance
            relevant_chunks.append((chunk_text, similarity, chunk_embedding))
            
            cur.close()
            conn.close()
        
        return relevant_chunks

# Example usage:
if __name__ == "__main__":
    # Initialize components
    config = DBConfig(
        dbname='code_embeddings',
        user='postgres',
        password='password',
        host='localhost',
        port=5432
    )
    
    chunker = TextChunker(max_chunk_size=512)
    embeddings_generator = EmbeddingsGenerator()
    vector_db = VectorDB(config)
    vector_db.build_faiss_index()
    
    # Initialize RAG retriever
    retriever = RAGRetriever(vector_db)
    
    # Test the retriever
    query = "How do I use the new product feature?"
    relevant_context = retriever.retrieve_relevant_context(query, k=3)
    
    for chunk, similarity in relevant_context:
        print(f"Relevance: {similarity:.2f}")
        print(chunk)
        print()