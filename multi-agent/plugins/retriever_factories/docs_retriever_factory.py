from typing import Any
from plugins.decorators import register_element
from plugins.base_factory import BaseFactory
from plugins.exceptions import PluginConfigurationError
from retrievers.models.retriever_config import DocsRetrieverConfig
from retrievers.docs_retriever import DocsRetriever


@register_element(
    category=DocsRetrieverConfig.Meta.category,
    type_key=DocsRetrieverConfig.Meta.type,
    config_schema=DocsRetrieverConfig,
    description=DocsRetrieverConfig.Meta.description
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
