from abc import ABC, abstractmethod
from dataclasses import asdict
import logging
from shared.logger import logger
from utils.monitor.pipeline_monitor import PipelineMonitor
from utils.embedding.embedding_generator_factory import EmbeddingGeneratorFactory
from pipeline.config import EmbeddingConfig, StorageConfig
from utils.storage.qdrant_storage import QdrantStorage
from utils.storage.mongo.mongo_helpers import get_mongo_storage
from utils.storage.vector_storage_factory import VectorStorageFactory
from typing import Any, Dict, List, Tuple, Type
from utils.storage.storage_manager import StorageManager
from functools import cached_property
from global_utils.utils.util import get_mongo_url
import pymongo

class PipelineFactory(ABC):
    """
    Base factory that instantiates the five pipeline layers:
        1. orchestrator
        2. collector
        3. processor
        4. chunker and embedder
        5. storage

    Subclasses must implement each `_create_*` method.
    After construction, `self.collector`, `self.processor`, etc. are ready to use.
    """
    SOURCE_TYPE: str
    _registry: Dict[str, Type["PipelineFactory"]] = {} 
     
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if ABC not in cls.__bases__:
            PipelineFactory._registry[cls.SOURCE_TYPE] = cls
            
    @classmethod
    def create(cls, source_type: str, metadata: Any) -> "PipelineFactory":
        try:
            factory_cls = cls._registry[source_type]
        except KeyError:
            raise ValueError(f"No PipelineFactory for {source_type!r}")
        return factory_cls(metadata)
    
    def __init__(self, metadata: Any):
        self.metadata = metadata
        self.orchestrator = self._create_orchestrator
        self.collector = self._create_collector
        self.processor = self._create_processor
        self.chunker_and_embedder = self._create_chunker_and_embedder
        self.storage   = self._create_storage
      
    @cached_property
    def embedder(self) -> Any:
        cfg = EmbeddingConfig()
        return EmbeddingGeneratorFactory.create(asdict(cfg)) 
    
    @cached_property
    def qdrant_client(self):
        base_cfg = asdict(StorageConfig(collection_name=f"{self.SOURCE_TYPE.lower()}_data"))
        base_cfg["embedding_dim"] = self.embedder.embedding_dim
        qstore = VectorStorageFactory.create(base_cfg)
        qstore.initialize()
        if not isinstance(qstore, QdrantStorage):
            raise RuntimeError("Expected QdrantStorage instance")
        return qstore
    
    @cached_property
    def mongo_client(self):
        return get_mongo_storage()
    
    @cached_property
    def storage_manager(self) -> StorageManager:
        return StorageManager(self.qdrant_client, self.mongo_client)
    
    @abstractmethod
    def _get_source_id(self) -> str:
        """Return the source id of the data source"""
        ...
    
    @abstractmethod
    def _get_source_name(self) -> str:
        """Return the source name of the data source"""
        ...
        
    def _get_monitor(self) -> PipelineMonitor:
        """Return an instance of your Monitor"""
        logging.getLogger(__name__).info(f"Getting monitor for {get_mongo_url()}")
        return PipelineMonitor(pymongo.MongoClient(get_mongo_url()))
    
    @abstractmethod
    def _create_summary(self) -> Dict:
        """Return a data source specific summary of the pipeline"""
        ...
               
    @abstractmethod
    def _create_orchestrator(self):
        """Return an instance of orchestrator"""
        ...

    @abstractmethod
    def _create_collector(self):
        """Return an instance of DataCollector"""
        ...

    @abstractmethod
    def _create_processor(self, data: Any):
        """Return an instance of your DataProcessor"""
        ...

    @abstractmethod
    def _create_chunker_and_embedder(self, processed: Any):
        """Return an instance of your Chunker strategy"""
        ...


    def _create_storage(self, pipeline_id: str, embeddings: Any):
        """Return an instance of your Storage backend"""
        return self.storage_manager.persist(
            pipeline_id=pipeline_id,
            source_id=self._get_source_id(),
            source_name=self._get_source_name(),
            source_type=self.SOURCE_TYPE,
            enriched_chunks=embeddings,
            summary=self._create_summary()
        )
        
    @abstractmethod
    def _clean_orchestrator(self):
        """Clean up the orchestrator"""
        ...
    
    