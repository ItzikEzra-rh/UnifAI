from typing import Any, Dict, List, Literal
from pydantic import BaseModel, ValidationError, Field
from plugins.base_factory import BaseFactory
from plugins.exceptions import PluginConfigurationError
from agents.pdf_agent import PDFAgent

class PDFRetrieverConfig(BaseModel):
    """
    Configuration schema for the PDF retriever.
    """
    name: str
    type: Literal["pdf"] = Field("pdf", const=True)
    documents: List[str]  # Paths or URIs to PDF documents


class PDFRetrieverFactory(BaseFactory):
    """
    Factory for constructing PDF-based retrievers.
    Loads PDFAgent instances that read and index given documents.
    """

    def accepts(self, cfg: Dict[str, Any]) -> bool:
        """
        Returns True if this factory can handle the given config.
        """
        return cfg.get("type") == "pdf"

    def create(self, cfg: Dict[str, Any]) -> PDFAgent:
        """
        Validate config and instantiate a PDFAgent.

        :param cfg: Raw config dict with keys 'name', 'type', 'documents'.
        :raises PluginConfigurationError: on validation or instantiation failure.
        :return: PDFAgent instance.
        """
        # 1. Validate config via Pydantic
        try:
            data = PDFRetrieverConfig(**cfg)
        except ValidationError as ve:
            raise PluginConfigurationError("Invalid PDF retriever config", cfg) from ve

        # 2. Instantiate the agent
        try:
            agent = PDFAgent(documents=data.documents)
        except Exception as e:
            raise PluginConfigurationError(f"Failed to create PDFAgent: {e}", cfg) from e

        return agent