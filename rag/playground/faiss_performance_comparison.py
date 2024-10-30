# Search Performance Comparison = Here's a practical example showing the difference in search performance:
import time
import numpy as np
import faiss

def performance_comparison(query_vector, stored_vectors, k=5):
    # Prepare data
    dimension = len(query_vector)
    
    # 1. Naive approach
    start_time = time.time()
    distances = np.linalg.norm(stored_vectors - query_vector, axis=1)
    naive_indices = np.argsort(distances)[:k]
    naive_time = time.time() - start_time
    
    # 2. FAISS approach
    index = faiss.IndexFlatL2(dimension)
    index.add(stored_vectors)
    
    start_time = time.time()
    D, I = index.search(query_vector.reshape(1, -1), k)
    faiss_time = time.time() - start_time
    
    return {
        "naive_time": naive_time,
        "faiss_time": faiss_time
    }

# Example with 1 million vectors
vectors = np.random.random((1_000_000, 384)).astype('float32')
query = np.random.random(384).astype('float32')

results = performance_comparison(query, vectors)
print(f"Naive search time: {results['naive_time']:.4f} seconds")
print(f"FAISS search time: {results['faiss_time']:.4f} seconds")