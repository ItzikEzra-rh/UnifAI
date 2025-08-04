from functools import cached_property
from typing import Dict, List
from shared.source_types import DocumentMetadata
from pipeline.pipeline_factory import PipelineFactory
from data_sources.docs.doc_config_manager import DocConfigManager
from data_sources.docs.doc_connector import DocumentConnector
from data_sources.docs.document_processor import DocumentProcessor
from data_sources.docs.pdf_chunker_strategy import PDFChunkerStrategy
from shared.config import ChunkerConfig
from config.constants import DataSource

class DocumentPipelineFactory(PipelineFactory):
    SOURCE_TYPE = DataSource.DOCUMENT.upper_name
    
    def __init__(
        self,
        metadata: DocumentMetadata,
    ):
        super().__init__(metadata)
        self._collected_data = None  # Cache for collected data

    @cached_property
    def doc_config(self) -> DocConfigManager:
        config = DocConfigManager()
        config.set_config_value("chunk_size", ChunkerConfig.chunk_size)
        config.set_config_value("chunk_overlap", ChunkerConfig.chunk_overlap)
        return config

    @cached_property
    def doc_chunker(self) -> PDFChunkerStrategy:
        return PDFChunkerStrategy(
            max_tokens_per_chunk=self.doc_config._config["chunk_size"],
            overlap_tokens=self.doc_config._config["chunk_overlap"]
        )

    def get_source_id(self) -> str:
        return self.metadata.doc_id

    def get_source_name(self) -> str:
        return self.metadata.doc_name or f"document_{self.metadata.doc_id}"
        
    def _create_summary(self) -> Dict:
        # Use cached collected data if available, otherwise return defaults
        if self._collected_data:
            return {
                "page_count": self._collected_data.get("metadata", {}).get("page_count", 0),
                "full_text": self._collected_data.get("text", ""),
                "file_size": self._collected_data.get("metadata", {}).get("file_size", 0),
            }
        else:
            return {
                "page_count": 0,
                "full_text": "",
                "file_size": 0,
            }

    def _create_collector(self):
        collected_data = DocumentConnector(self.doc_config).process_document(
            document_path=self.metadata.doc_path,
            upload_by=self.metadata.upload_by
        )
        # Cache the collected data for use in summary
        self._collected_data = collected_data
        return collected_data

    def _create_processor(
        self,
        data: Dict
    ) -> Dict:
        return DocumentProcessor().process(
            data,
            clean_markdown=False,
            clean_text=False,
            remove_references=False,
            preserve_original=True
        )

    def _create_chunker_and_embedder(
        self,
        processed: Dict,
    ) -> List[Dict]:
        # Prepare for embedding
        embedding_ready_docs = DocumentProcessor().prepare_for_single_doc_embedding(processed)
        
        # Chunk the content
        chunks = self.doc_chunker.chunk_content([embedding_ready_docs])
        # Generate embeddings
        return self.embedder.generate_embeddings(chunks)