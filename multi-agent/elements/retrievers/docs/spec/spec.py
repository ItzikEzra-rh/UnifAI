from elements.common.base_element_spec import BaseElementSpec
from core.enums import ResourceCategory
from ..config import DocsRetrieverConfig
from ..docs_retriever_factory import DocsRetrieverFactory

class DocsRetrieverElementSpec(BaseElementSpec):
    """Element specification for Docs Retriever."""

    category = ResourceCategory.RETRIEVER
    type_key = "docs"
    name = "Docs Retriever"
    description = "Fetches relevant document passages for a query"
    config_schema = DocsRetrieverConfig
    factory_cls = DocsRetrieverFactory
    tags = ["retriever", "docs", "search", "query", "information retrieval"]