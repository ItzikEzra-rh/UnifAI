from functools import cached_property
from typing import Dict, List
from pipeline.types import DocumentMetadata
from pipeline.pipeline_factory import PipelineFactory
from pipeline.decorators import inject
from data_sources.docs.doc_config_manager import DocConfigManager
from data_sources.docs.doc_connector import DocumentConnector
from data_sources.docs.document_processor import DocumentProcessor
from data_sources.docs.pdf_chunker_strategy import PDFChunkerStrategy
from pipeline.config import ChunkerConfig
from shared.logger import logger
from config.constants import DataSource

class DocumentPipelineFactory(PipelineFactory):
    SOURCE_TYPE = DataSource.DOCUMENT.upper_name
    
    def __init__(
        self,
        metadata: DocumentMetadata,
    ):
        super().__init__(metadata)

    @cached_property
    def doc_config(self) -> DocConfigManager:
        config = DocConfigManager()
        config.set_config_value("chunk_size", 800)
        config.set_config_value("chunk_overlap", 100)
        return config

    @cached_property
    def connector(self) -> DocumentConnector:
        return DocumentConnector(self.doc_config)

    @cached_property
    def doc_processor(self) -> DocumentProcessor:
        return DocumentProcessor()

    @cached_property
    def doc_chunker(self) -> PDFChunkerStrategy:
        return PDFChunkerStrategy(
            max_tokens_per_chunk=self.doc_config._config["chunk_size"],
            overlap_tokens=self.doc_config._config["chunk_overlap"]
        )

    def _get_source_id(self) -> str:
        return self.metadata.doc_id

    def _get_source_name(self) -> str:
        return self.metadata.doc_name or f"doc_{self.metadata.doc_id}"
        
    def _create_summary(self) -> Dict:
        return {
            "doc_path": self.metadata.doc_path,
            "upload_by": self.metadata.upload_by,
        }
        
    def _create_orchestrator(self):
        self._get_monitor().start_log_monitoring(target_logger=logger, pipeline_id=f"doc_{self.metadata.doc_id}")
 
    @inject('connector')
    def _create_collector(self, connector) -> Dict:
        return connector.process_document(
            doc_path=self.metadata.doc_path,
            upload_by=self.metadata.upload_by
        )

    @inject('doc_processor')
    def _create_processor(
        self,
        data: Dict,
        doc_processor
    ) -> Dict:
        return doc_processor.process(
            data,
            clean_markdown=False,
            clean_text=False,
            remove_references=False,
            preserve_original=True
        )

    @inject('doc_processor', 'doc_chunker', 'embedder')
    def _create_chunker_and_embedder(
        self,
        processed: Dict,
        doc_processor,
        doc_chunker,
        embedder
    ) -> List[Dict]:
        # Prepare for embedding
        embedding_ready_docs = doc_processor.prepare_for_single_doc_embedding(processed)
        
        # Chunk the content
        chunks = doc_chunker.chunk_content([embedding_ready_docs])
        
        # Add metadata to chunks
        for idx, chunk in enumerate(chunks):
            md = chunk.setdefault("metadata", {})
            md.update({
                "source_id": self.metadata.doc_id,
                "chunk_index": idx,
                "source_type": DataSource.DOCUMENT.upper_name,
                "doc_name": self.metadata.doc_name,
                "doc_path": self.metadata.doc_path,
            })

        # Generate embeddings
        return embedder.generate_embeddings(chunks)

    def _clean_orchestrator(self):
        self._get_monitor().finish_log_monitoring() 