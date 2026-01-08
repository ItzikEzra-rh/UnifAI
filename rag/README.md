# RAG Module

> **Data Pipeline Hub** — Hexagonal architecture implementation for document and Slack data ingestion with vector search capabilities.

## Overview

The RAG (Retrieval-Augmented Generation) module handles data ingestion pipelines for multiple source types, processing content into vector embeddings for semantic search. Built with **Hexagonal Architecture** (Ports & Adapters) for maximum testability, maintainability, and flexibility.

### Key Features

- 📄 **Document Processing** — PDF, Markdown ingestion with intelligent chunking
- 💬 **Slack Integration** — Channel and thread message indexing
- 🔍 **Vector Search** — Semantic similarity search via Qdrant
- ⚡ **Async Pipelines** — Celery-based background task execution
- 🔌 **Pluggable Adapters** — Easy to swap MongoDB, Qdrant, or add new sources

---

## Architecture

```
rag/
├── domain/          # 🎯 Core business logic (pure Python, no external deps)
├── application/     # 📦 Use cases & orchestration services  
├── infrastructure/  # 🔌 Adapters (Mongo, Qdrant, Celery, HTTP)
├── bootstrap/       # ⚡ Dependency injection & app setup
├── config/          # ⚙️ Configuration management
├── shared/          # 🔧 Cross-cutting utilities (logging)x
```

### Layer Responsibilities

| Layer | Purpose | Dependencies |
|-------|---------|--------------|
| **Domain** | Business rules, entities, port interfaces | None (pure Python) |
| **Application** | Use cases, service orchestration | Domain only |
| **Infrastructure** | External system adapters | Domain + external libs |
| **Bootstrap** | Wiring, DI container, app factory | All layers |

### Dependency Flow

```
Infrastructure ───────▶ Domain ◀──────── Application
   (Adapters)            (Ports)          (Services)

              Both depend on abstractions,
                 not on each other!
```

📖 **See [rag.md](./rag.md) for detailed architecture diagrams and class relationships.**

---

## Quick Start

### Prerequisites

- Python 3.10+
- MongoDB (running on localhost:27017)
- Qdrant (running on localhost:6333)
- RabbitMQ (running on localhost:5672)

### Installation

```bash
cd rag

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install package in development mode
pip install -e .
```

### Environment Variables

Create a `.env` file or export these variables:

### Running the Server

```bash
# Development server
python -m bootstrap.flask_app

```

### Running Celery Workers

```bash
# Start pipeline worker
celery -A infrastructure.celery.app worker -Q document_queue,slack_queue -l info

# Start event worker (Slack events)
celery -A infrastructure.celery.app worker -Q slack_events -l info
```

---

## Core Components

### Domain Layer

The domain layer contains pure business logic with no external dependencies.

#### Ports (Interfaces)

| Port | Purpose |
|------|---------|
| `VectorRepository` | Vector storage operations (store, search, delete) |
| `PipelineRepository` | Pipeline state management |
| `DataSourceRepository` | Data source metadata storage |
| `ContentChunker` | Text chunking strategies |
| `EmbeddingGenerator` | Vector embedding generation |
| `SourcePipelinePort` | Source-specific pipeline operations |

#### Models (Entities)

| Model | Description |
|-------|-------------|
| `PipelineRecord` | Pipeline execution state and stats |
| `DataSource` | Registered data source metadata |
| `VectorChunk` | Text chunk with embedding vector |
| `SearchResult` | Vector similarity search result |

### Application Layer

Use cases that orchestrate domain objects to fulfill business requirements.

| Service | Responsibility |
|---------|----------------|
| `PipelineService` | Pipeline lifecycle management |
| `PipelineDispatchService` | Registration + async task dispatch |
| `DataSourceService` | Data source CRUD operations |
| `RetrievalService` | Vector search orchestration |
| `MonitoringService` | Pipeline metrics and logging |
| `RegistrationService` | Source registration with validation |
| `FileValidationService` | Pre-upload file validation |

#### Pipeline Handlers

| Handler | Source Type |
|---------|-------------|
| `DocumentPipelineHandler` | PDF, Markdown files |
| `SlackPipelineHandler` | Slack channels and threads |

### Infrastructure Layer

Concrete implementations of domain ports using external technologies.

#### Storage Adapters

| Adapter | Technology | Implements |
|---------|------------|------------|
| `MongoPipelineRepository` | MongoDB | `PipelineRepository` |
| `MongoDataSourceRepository` | MongoDB | `DataSourceRepository` |
| `QdrantVectorRepository` | Qdrant | `VectorRepository` |

#### Processing Adapters

| Adapter | Purpose |
|---------|---------|
| `SentenceTransformerEmbedder` | Text → vector embeddings |
| `PDFChunkerStrategy` | PDF text chunking |
| `SlackChunkerStrategy` | Conversation-aware chunking |
| `DocumentConnector` | PDF/Markdown file loading |
| `SlackConnector` | Slack API integration |

#### HTTP Adapters (Blueprints)

| Endpoint | Path Prefix |
|----------|-------------|
| `/health` | Health checks |
| `/docs` | Document operations |
| `/slack` | Slack operations |
| `/pipelines` | Pipeline management |
| `/data-sources` | Data source management |
| `/vector` | Vector statistics |
| `/settings` | Configuration |

#### Async Adapters

| Adapter | Purpose |
|---------|---------|
| `CeleryPipelineDispatcher` | Dispatch pipeline tasks |
| `CelerySlackEventDispatcher` | Dispatch Slack event handlers |

---

## Dependency Injection

All dependencies are wired in `bootstrap/app_container.py` using `@lru_cache` for singleton management.

### Usage

```python
from bootstrap.app_container import (
    pipeline_service,
    data_source_service,
    retrieval_service,
)

# Services are singletons - same instance on every call
svc = pipeline_service()
result = svc.get(pipeline_id)

# Parameterized singletons
retriever = retrieval_service("DOCUMENT")  # One per source type
```

### Available Factories

```python
# Infrastructure (shared resources)
mongo_client()              # MongoDB connection pool
file_storage()              # Local file storage

# Repositories
pipeline_repository()       # Pipeline state storage
data_source_repository()    # Data source metadata
vector_repository(name)     # Vector storage (per collection)

# Services
pipeline_service()          # Pipeline lifecycle
data_source_service()       # Data source CRUD
monitoring_service()        # Metrics & logging
retrieval_service(type)     # Vector search

# Pipeline Components
embedding_generator()       # Sentence transformer
pdf_chunker()              # Document chunking
slack_chunker()            # Conversation chunking
document_connector()        # File loading
slack_connector(project)    # Slack API client
```

---

## API Endpoints

### Health

```
GET /health           → Service health status
```

### Documents

```
POST   /docs/upload   → Upload document(s)
GET    /docs          → List documents (paginated)
DELETE /docs/{id}     → Delete document
```

### Slack

```
POST   /slack/channels      → Register Slack channels
GET    /slack/channels      → List registered channels
DELETE /slack/channels/{id} → Remove channel
POST   /slack/events        → Slack Events API webhook
```

### Pipelines

```
GET    /pipelines           → List all pipelines
GET    /pipelines/{id}      → Get pipeline status
DELETE /pipelines/{id}      → Cancel/delete pipeline
```

### Vector Search

```
POST   /vector/search       → Semantic search
GET    /vector/stats        → Vector storage statistics
```

---

## Configuration

Configuration is managed via `config/app_config.py` with environment variable overrides.

| Config Key | Env Variable | Default | Description |
|------------|--------------|---------|-------------|
| `mongodb_ip` | `MONGODB_IP` | `0.0.0.0` | MongoDB host |
| `mongodb_port` | `MONGODB_PORT` | `27017` | MongoDB port |
| `qdrant_ip` | `QDRANT_URL` | `0.0.0.0` | Qdrant host |
| `qdrant_port` | `QDRANT_PORT` | `6333` | Qdrant port |
| `rabbitmq_ip` | `RABBITMQ_IP` | `0.0.0.0` | RabbitMQ host |
| `port` | `PORT` | `13457` | Server port |
| `upload_folder` | `UPLOAD_FOLDER` | `/app/shared` | File upload path |

---

## Data Flow

### Document Pipeline

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────────┐
│   Upload    │────▶│  Validate &  │────▶│   Celery    │────▶│   Execute    │
│   Request   │     │   Register   │     │   Queue     │     │   Pipeline   │
└─────────────┘     └──────────────┘     └─────────────┘     └──────┬───────┘
                                                                     │
                    ┌──────────────┐     ┌─────────────┐     ┌───────▼───────┐
                    │    Store     │◀────│   Embed     │◀────│    Chunk      │
                    │   (Qdrant)   │     │   (384-dim) │     │   (500 tok)   │
                    └──────────────┘     └─────────────┘     └───────────────┘
```

### Search Flow

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────────┐
│   Query     │────▶│    Embed     │────▶│   Vector    │────▶│   Return     │
│   Text      │     │    Query     │     │   Search    │     │   Results    │
└─────────────┘     └──────────────┘     └─────────────┘     └──────────────┘
```

---

## Extending

### Adding a New Data Source

1. **Domain Model**: Create `domain/<source>/model.py`
2. **Repository Port**: Define interface in `domain/<source>/repository.py`
3. **Pipeline Handler**: Implement `SourcePipelinePort` in `application/pipeline/<source>_handler.py`
4. **Infrastructure Adapters**: Add connectors, chunkers in `infrastructure/`
5. **Wire Dependencies**: Add factories to `bootstrap/app_container.py`
6. **HTTP Endpoints**: Create blueprint in `infrastructure/http/<source>.py`

### Swapping an Adapter

To replace Qdrant with Pinecone: "Example"

1. Create `infrastructure/pinecone/pinecone_vector_repository.py`
2. Implement `VectorRepository` interface
3. Update `bootstrap/factories.py` to use new adapter
4. No changes needed in domain or application layers ✅

---

## Project Structure Details

```
rag/
├── domain/
│   ├── connector/          # Data source connector interface
│   ├── data_source/        # Data source model & repository
│   ├── monitoring/         # Metrics model & repository
│   ├── pagination/         # Pagination model
│   ├── pipeline/           # Pipeline model, repository, port, dispatcher
│   ├── processor/          # Data processors (document, slack)
│   ├── registration/       # Registration model & port
│   ├── slack_channel/      # Slack channel model & repository
│   ├── slack_event/        # Slack event model, port, dispatcher
│   ├── validation/         # Validation model & port
│   └── vector/             # Vector model, repository, chunker, embedder
│
├── application/
│   ├── common/parsing/     # Log parsing utilities
│   ├── pipeline/           # Pipeline handlers & executor
│   ├── registration/       # Registration service & strategies
│   ├── slack_events/       # Slack event handlers
│   ├── stats/              # Statistics services
│   ├── validation/         # Validator pipeline
│   └── *.py                # Application services
│
├── infrastructure/
│   ├── celery/             # Celery app, dispatchers, workers
│   ├── chunking/           # Chunking strategies (PDF, Slack)
│   ├── config/             # Config managers
│   ├── connector/          # Data connectors (Document, Slack)
│   ├── embedding/          # Embedding generators
│   ├── http/               # Flask blueprints
│   ├── mongo/              # MongoDB repositories
│   ├── qdrant/             # Qdrant vector repository
│   ├── retrieval/          # Search filter resolvers
│   ├── storage/            # File storage
│   ├── umami/              # Analytics client
│   └── validation/         # Validation adapters
│
├── bootstrap/
│   ├── app_container.py    # Dependency injection container
│   ├── factories.py        # Component factories
│   └── flask_app.py        # Flask application factory
│
├── config/
│   └── app_config.py       # Application configuration
│
├── shared/
│   └── logger.py           # Logging utilities
│
├── requirements.txt        # Python dependencies
├── setup.py               # Package setup
└── rag.md                 # Architecture diagrams
```

---

## Dependencies

| Package | Purpose |
|---------|---------|
| `flask` | HTTP framework |
| `qdrant-client` | Vector database client |
| `sentence-transformers` | Embedding generation |
| `docling` | Document parsing |
| `langchain` | LLM utilities |
| `celery` | Async task queue |
| `pymongo` | MongoDB driver |

---


