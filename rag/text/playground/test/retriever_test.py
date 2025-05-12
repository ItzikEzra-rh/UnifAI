from rag.text.rag_processor import RAGProcessor
from retrievers.rag_retriever import RAGRetriever
from db.vector_db import DBConfig, VectorDB
from chunking.text_chunker import TextChunker
from embeddings.embeddings_generator import EmbeddingsGenerator
import time
import base64
import numpy as np

"""
The RAGProcessor will process a file, store the embeddings in the database, and build the FAISS index.
The RAGRetriever can then be used to retrieve the most relevant context for a given query.
"""
# Initialize components
config = DBConfig(
    dbname='code_embeddings',
    user='postgres',
    password='password',
    host='localhost',
    port=5432
)

chunker = TextChunker(max_chunk_size=128)
embeddings_generator = EmbeddingsGenerator()
vector_db = VectorDB(config)
vector_db.initialize_db()

# Initialize RAG processor
processor = RAGProcessor(chunker, embeddings_generator, vector_db)

# Process a file
processor_start_time = time.time()
processor.process_file(
    file_path="/home/cloud-user/Projects/playGround/tree-sitter-playground/docs/AIM.txt",
    metadata={"project": "AIM", "version": "1.0"}
)

processor_end_time = time.time()
processor_execution_time = processor_end_time - processor_start_time
print("FINISHED: RAGProcessor: processor")
print(f"Function 'RAGProcessor: processor' executed in {processor_execution_time:.4f} seconds")

# # Active it when not process a file:
# processor.vector_db.build_faiss_index()

retriever_start_time = time.time()
retriever = RAGRetriever(processor.vector_db)
# query = "Tell me about 2019 Asian Cup final?"
# query = "What is football?"
# query = "What are the statistics in stats collector used in AIM?"
query = "What is AIM?"
relevant_context = retriever.retrieve_relevant_context(query, k=5)

retriever_end_time = time.time()
retriever_execution_time = retriever_end_time - retriever_start_time
print("FINISHED: RAGRetriever: processor")
print(f"Function 'RAGRetriever: processor' executed in {retriever_execution_time:.4f} seconds")

for chunk, similarity, embedding in relevant_context:
    try:
        print(f"Relevance: {similarity:.2f}")
        print(chunk)  # should print as a readable string if decoding is correct
        print()
    except Exception:
        print(type(chunk))    

"""
Integrate with your LLM: We can use the retrieved relevant context to augment the input for our LLM, potentially improving the quality of the responses.

# Example integration with an LLM
llm = YourLLMModel()
query = "How do I use the new product feature?"
relevant_context = retriever.retrieve_relevant_context(query, k=3)

# Concatenate the query and relevant context
augmented_input = "\n".join([query] + [chunk for chunk, _ in relevant_context])

response = llm.generate(augmented_input)
print(response)
"""