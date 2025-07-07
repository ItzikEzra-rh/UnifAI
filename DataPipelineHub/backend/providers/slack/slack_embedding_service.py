"""
Modern Slack Embedding Service

A clean, maintainable refactor of the embed_slack_channels_flow function
with proper separation of concerns and modern Python practices.
"""

import time
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Protocol
from contextlib import contextmanager
from abc import ABC, abstractmethod

import pymongo
from shared.logger import logger
from global_utils.utils.util import get_mongo_url
from utils.storage.mongo.mongo_helpers import get_mongo_storage
from utils.storage.storage_manager import StorageManager
from utils.storage.qdrant_storage import QdrantStorage
from utils.storage.vector_storage_factory import VectorStorageFactory
from utils.embedding.embedding_generator_factory import EmbeddingGeneratorFactory
from data_sources.slack.slack_connector import SlackConnector
from data_sources.slack.slack_data_processor import SlackProcessor
from data_sources.slack.slack_chunker_strategy import SlackChunkerStrategy
from data_sources.slack.slack_pipeline_scheduler import SlackDataPipeline
from config.constants import DataSource

@dataclass
class ChannelData:
    """Represents a Slack channel to be embedded."""
    channel_id: str
    channel_name: str
    is_private: bool


@dataclass
class ProcessingResult:
    """Represents the result of processing a single channel."""
    channel_name: str
    status: str
    chunks_stored: int = 0
    error: Optional[str] = None


@dataclass
class EmbeddingConfig:
    """Configuration for embedding generation."""
    type: str = "sentence_transformer"
    model_name: str = "all-MiniLM-L6-v2"
    batch_size: int = 32
    max_tokens_per_chunk: int = 500
    overlap_tokens: int = 50
    time_window_seconds: int = 300


@dataclass
class StorageConfig:
    """Configuration for vector storage."""
    type: str = "qdrant"
    collection_name: str = "slack_data"


class SlackChannelProcessor(Protocol):
    """Protocol for processing Slack channels."""
    
    def process_channel(self, channel: ChannelData, pipeline_id: str) -> ProcessingResult:
        """Process a single Slack channel."""
        ...


class SlackEmbeddingService:
    """
    Slack embedding service.
    
    This service handles the embedding of Slack channels with proper
    separation of concerns and dependency injection.
    """
    
    def __init__(
        self,
        connector: SlackConnector,
        config: EmbeddingConfig,
        upload_by: str = "default"
    ):
        self.connector = connector
        self.config = config
        self.upload_by = upload_by
        self._setup_dependencies()
    
    def _setup_dependencies(self) -> None:
        """Initialize all required dependencies."""
        # Storage components
        self.mongo_client = pymongo.MongoClient(get_mongo_url())
        self.mongo_storage = get_mongo_storage()
        self.pipeline = SlackDataPipeline(self.mongo_client, logger=logger)
        
        # Processing components
        self.processor = SlackProcessor()
        self.chunker = SlackChunkerStrategy(
            max_tokens_per_chunk=self.config.max_tokens_per_chunk,
            overlap_tokens=self.config.overlap_tokens,
            time_window_seconds=self.config.time_window_seconds
        )
        
        # Embedding components
        self.embedding_generator = EmbeddingGeneratorFactory.create({
            "type": self.config.type,
            "model_name": self.config.model_name,
            "batch_size": self.config.batch_size
        })
        
        # Vector storage
        self.vector_store = self._setup_vector_storage()
        self.storage_manager = StorageManager(self.vector_store, self.mongo_storage)
    
    def _setup_vector_storage(self) -> QdrantStorage:
        """Setup and initialize vector storage."""
        storage_config = {
            "type": "qdrant",
            "collection_name": "slack_data",
            "embedding_dim": self.embedding_generator.embedding_dim
        }
        qstore = VectorStorageFactory.create(storage_config)
        qstore.initialize()
        
        if not isinstance(qstore, QdrantStorage):
            raise RuntimeError("Expected QdrantStorage instance")
        
        return qstore
    
    def embed_channels(self, channel_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Embed a list of Slack channels.
        
        Args:
            channel_list: List of channel dictionaries
            
        Returns:
            List of processing results
        """
        if not self.connector.authenticate():
            raise RuntimeError("Slack authentication failed")
        
        channels = [
            ChannelData(
                channel_id=ch["channel_id"],
                channel_name=ch["channel_name"],
                is_private=ch["is_private"]
            )
            for ch in channel_list
        ]
        
        results = []
        for channel in channels:
            try:
                result = self._process_single_channel(channel)
                results.append(result.to_dict())
            except Exception as e:
                logger.error(f"Failed to process channel {channel.channel_name}: {e}")
                results.append(ProcessingResult(
                    channel_name=channel.channel_name,
                    status="failed",
                    error=str(e)
                ).to_dict())
        
        return results
    
    def _process_single_channel(self, channel: ChannelData) -> ProcessingResult:
        """Process a single Slack channel."""
        processor = SingleChannelProcessor(
            channel=channel,
            connector=self.connector,
            pipeline=self.pipeline,
            processor=self.processor,
            chunker=self.chunker,
            embedding_generator=self.embedding_generator,
            vector_store=self.vector_store,
            mongo_storage=self.mongo_storage
        )
        
        return processor.process()


class SingleChannelProcessor:
    """Handles processing of a single Slack channel."""
    
    def __init__(
        self,
        channel: ChannelData,
        connector: SlackConnector,
        pipeline: SlackDataPipeline,
        processor: SlackProcessor,
        chunker: SlackChunkerStrategy,
        embedding_generator,
        vector_store: QdrantStorage,
        mongo_storage
    ):
        self.channel = channel
        self.connector = connector
        self.pipeline = pipeline
        self.processor = processor
        self.chunker = chunker
        self.embedding_generator = embedding_generator
        self.vector_store = vector_store
        self.mongo_storage = mongo_storage
        self.pipeline_id = None
    
    def process(self) -> ProcessingResult:
        """Process the channel and return the result."""
        try:
            with self._monitoring_context():
                return self._execute_processing()
        except Exception as e:
            logger.error(f"Error processing channel {self.channel.channel_name}: {e}")
            self._handle_error(str(e))
            return ProcessingResult(
                channel_name=self.channel.channel_name,
                status="failed",
                error=str(e)
            )
    
    @contextmanager
    def _monitoring_context(self):
        """Context manager for pipeline monitoring."""
        self.pipeline_id = self.pipeline.process_slack_channel(
            self.channel.channel_id,
            self.channel.channel_name
        )
        
        self.pipeline.monitor.start_log_monitoring(
            target_logger=logger,
            pipeline_id=f"slack_{self.channel.channel_id}"
        )
        
        try:
            yield
            self.pipeline.monitor.finish_log_monitoring()
        except Exception:
            if self.pipeline_id:
                self.pipeline.monitor.record_error(self.pipeline_id, "Processing failed")
            raise
    
    def _execute_processing(self) -> ProcessingResult:
        """Execute the main processing logic."""
        # 1. Register initial state
        self._register_initial_state()
        
        # 2. Fetch messages
        messages, thread_msgs = self.connector.get_conversations_history(self.channel.channel_id)
        
        # 3. Update with message count
        self._update_message_count(len(messages))
        
        # 4. Process and chunk
        all_chunks = self._process_and_chunk_messages(messages, thread_msgs)
        
        # 5. Generate embeddings and store
        embeddings = self._generate_and_store_embeddings(all_chunks)
        
        # 6. Update final state
        self._update_final_state(len(messages), len(all_chunks), len(embeddings))
        
        return ProcessingResult(
            channel_name=self.channel.channel_name,
            status="success",
            chunks_stored=len(all_chunks)
        )
    
    def _register_initial_state(self) -> None:
        """Register the channel with initial state."""
        self.mongo_storage.upsert_source_summary(
            source_id=self.channel.channel_id,
            source_name=self.channel.channel_name,
            source_type=DataSource.SLACK.upper_name,
            summary=self._create_summary(0, 0, 0),
            type_data=self._create_type_data(0, 0)
        )
    
    def _update_message_count(self, message_count: int) -> None:
        """Update the source with message count."""
        self.mongo_storage.upsert_source_summary(
            source_id=self.channel.channel_id,
            source_name=self.channel.channel_name,
            source_type=DataSource.SLACK.upper_name,
            summary=self._create_summary(0, 0, 0),
            type_data=self._create_type_data(message_count, 0)
        )
    
    def _process_and_chunk_messages(self, messages: List, thread_msgs: List) -> List[Dict[str, Any]]:
        """Process messages and create chunks."""
        # Process main messages
        processed_main = self.processor.process(messages, channel_name=self.channel.channel_name)
        
        # Process thread messages
        processed_threads = [
            self.processor.process(thread, channel_name=self.channel.channel_name)
            for thread in thread_msgs
        ]
        
        # Create chunks
        all_chunks = self.chunker.chunk_content(processed_main)
        for thread in processed_threads:
            all_chunks.extend(thread)
        
        # Add metadata
        return self._add_metadata_to_chunks(all_chunks)
    
    def _add_metadata_to_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Add source metadata to chunks."""
        for i, chunk in enumerate(chunks):
            if "metadata" not in chunk:
                chunk["metadata"] = {}
            
            chunk["metadata"].update({
                "source_id": self.channel.channel_id,
                "source_type": DataSource.SLACK.upper_name,
                "chunk_index": i
            })
        
        return chunks
    
    def _generate_and_store_embeddings(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate embeddings and store them."""
        embeddings = self.embedding_generator.generate_embeddings(chunks)
        self.vector_store.store_embeddings(embeddings)
        return embeddings
    
    def _update_final_state(self, message_count: int, chunk_count: int, embedding_count: int) -> None:
        """Update the source with final processing results."""
        api_calls = self._get_api_calls_count()
        
        self.mongo_storage.upsert_source_summary(
            source_id=self.channel.channel_id,
            source_name=self.channel.channel_name,
            source_type=DataSource.SLACK.upper_name,
            summary=self._create_summary(chunk_count, embedding_count, 0),
            type_data=self._create_type_data(message_count, api_calls)
        )
    
    def _handle_error(self, error_message: str) -> None:
        """Handle processing errors."""
        self.mongo_storage.upsert_source_summary(
            source_id=self.channel.channel_id,
            source_name=self.channel.channel_name,
            source_type=DataSource.SLACK.upper_name,
            summary={
                "chunks_generated": 0,
                "embeddings_created": 0,
                "processing_time_s": 0,
                "last_pipeline_id": self.pipeline_id,
                "status": "failed",
                "error": error_message
            },
            type_data=self._create_type_data(0, 0)
        )
    
    def _create_summary(self, chunks: int, embeddings: int, processing_time: float) -> Dict[str, Any]:
        """Create a summary dictionary."""
        return {
            "chunks_generated": chunks,
            "embeddings_created": embeddings,
            "processing_time_s": processing_time,
            "last_pipeline_id": self.pipeline_id,
        }
    
    def _create_type_data(self, message_count: int, api_calls: int) -> Dict[str, Any]:
        """Create type-specific data dictionary."""
        return {
            "message_count": message_count,
            "api_calls": api_calls,
            "is_private": self.channel.is_private
        }
    
    def _get_api_calls_count(self) -> int:
        """Get the number of API calls made."""
        if hasattr(self.pipeline, 'slack_monitor') and hasattr(self.pipeline.slack_monitor, 'get_api_calls'):
            return self.pipeline.slack_monitor.get_api_calls(self.pipeline_id)
        return 0


# Add method to ProcessingResult for backward compatibility
def _result_to_dict(self) -> Dict[str, Any]:
    """Convert result to dictionary for backward compatibility."""
    result = {
        "channel": self.channel_name,
        "status": self.status,
        "chunks_stored": self.chunks_stored
    }
    if self.error:
        result["error"] = self.error
    return result

ProcessingResult.to_dict = _result_to_dict


def embed_slack_channels_flow(channel_list: List[Dict[str, Any]], upload_by: str = "default") -> List[Dict[str, Any]]:
    """
    Slack embedding flow function that maintains backward compatibility.
    
    This function now delegates to the SlackEmbeddingService.
    """
    from providers.slack.slack import _get_configured_connector
    
    connector = _get_configured_connector()
    config = EmbeddingConfig()
    
    service = SlackEmbeddingService(
        connector=connector,
        config=config,
        upload_by=upload_by
    )
    
    return service.embed_channels(channel_list) 