## Overview

## Code Structure

- **FileHandler class:**
- Handles file operations and metadata
- Uses FileMetadata dataclass to store file information
- Responsible for reading and managing file content

- **TextChunker class:**
- Handles text chunking operations
- Configurable max_chunk_size
- Can work directly with FileHandler instances

- **EmbeddingsGenerator class:**
- Manages the transformer model and tokenizer
- Generates embeddings for text chunks
- Handles device (CPU/GPU) management

- **VectorDB class:**
- Manages database operations
- Uses DBConfig dataclass for configuration
- Handles both PostgreSQL and FAISS operations
- Stores metadata along with embeddings

- **RAGProcessor class:**
- Orchestrates the entire pipeline
- Combines all components into a single workflow
- Provides a simple interface for processing files

## Getting Started