from abc import ABC, abstractmethod
from dataclasses import asdict
from shared.logger import logger
from utils.monitor.pipeline_monitor import PipelineMonitor
from utils.embedding.embedding_generator_factory import EmbeddingGeneratorFactory
from shared.config import EmbeddingConfig, StorageConfig
from utils.storage.vector_storage_factory import VectorStorageFactory
from typing import Any, Dict, Type
from functools import cached_property
from global_utils.utils.util import get_mongo_url
import pymongo


class Pipeline:
    def __init__(
        self,
        orchestrator,
        collector,
        processor,
        chunker_and_embedder,
        storage,
        clean_orchestrator,
        summary,
        source_type,
        get_source_id,
        get_source_name
    ):
        self.orchestrator = orchestrator
        self.collector = collector
        self.processor = processor
        self.chunker_and_embedder = chunker_and_embedder
        self.storage = storage
        self.clean_orchestrator = clean_orchestrator
        self.summary = summary
        self.source_type = source_type
        self.get_source_id = get_source_id
        self.get_source_name = get_source_name
        
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
        self.monitor = PipelineMonitor(pymongo.MongoClient(get_mongo_url()))
          
    @cached_property
    def embedder(self) -> Any:
        cfg = EmbeddingConfig()
        return EmbeddingGeneratorFactory.create(asdict(cfg)) 
    
    @cached_property
    def vector_storage(self):
        base_cfg = asdict(StorageConfig(collection_name=f"{self.SOURCE_TYPE.lower()}_data"))
        base_cfg["embedding_dim"] = self.embedder.embedding_dim
        vector_storage = VectorStorageFactory.create(base_cfg)
        vector_storage.initialize()
        return vector_storage
    
    def create_pipeline(self) -> Pipeline:
        return Pipeline(
            orchestrator=self._create_orchestrator,
            collector=self._create_collector,
            processor=self._create_processor,
            chunker_and_embedder=self._create_chunker_and_embedder,
            storage=self._create_storage,
            clean_orchestrator=self._clean_orchestrator,
            summary=self._create_summary,
            source_type=self.SOURCE_TYPE,
            get_source_id=self.get_source_id,
            get_source_name=self.get_source_name
        )
    
    def _create_orchestrator(self):
        self.monitor.start_log_monitoring(target_logger=logger, pipeline_id=f"{self.SOURCE_TYPE.lower()}_{self.get_source_id()}")
        return self.monitor  # Return the monitor instance for the Pipeline object
    
    def _clean_orchestrator(self):
        """Clean up the orchestrator"""
        self.monitor.finish_log_monitoring()

    @abstractmethod
    def get_source_id(self) -> str:
        """Return the source id of the data source"""
        ...
    
    @abstractmethod
    def get_source_name(self) -> str:
        """Return the source name of the data source"""
        ...
        
    @abstractmethod
    def _create_summary(self) -> Dict:
        """Return a data source specific summary of the pipeline"""
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

    def _create_storage(self, embeddings: Any):
        """Store embeddings in vector storage"""
        return self.vector_storage.store_embeddings(embeddings)
        
    