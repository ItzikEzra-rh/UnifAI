from typing import Any
from plugins.decorators import register_element
from plugins.base_factory import BaseFactory
from plugins.exceptions import PluginConfigurationError
from schemas.retriever.retriever_config import DocsRetrieverConfig
from retrievers.docs_retriever import DocsRetriever


@register_element(
    category="retriever",
    type_key=DocsRetrieverConfig.model_fields["type"].default,
    config_schema=DocsRetrieverConfig,
    description="Docs‐based retriever via an external HTTP API"
)
class DocsRetrieverFactory(BaseFactory[DocsRetrieverConfig, DocsRetriever]):
    def accepts(self, cfg: DocsRetrieverConfig) -> bool:
        return cfg.type == "docs"

    def create(self, cfg: DocsRetrieverConfig, **kwargs: Any) -> DocsRetriever:
        try:
            return DocsRetriever(name=cfg.name,
                                 api_url=cfg.api_url,
                                 top_k_results=cfg.top_k_results,
                                 threshold=cfg.threshold)
        except Exception as e:
            raise PluginConfigurationError(
                f"DocsRetrieverFactory.create() failed: {e}", cfg.dict()
            ) from e
