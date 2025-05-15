from typing import Any
from plugins.decorators import register_element
from plugins.base_factory import BaseFactory
from plugins.exceptions import PluginConfigurationError
from schemas.retriever.retriever_config import SlackRetrieverConfig
from retrievers.slack_retriever import SlackRetriever


@register_element(
    category=SlackRetrieverConfig.Meta.category,
    type_key=SlackRetrieverConfig.Meta.type,
    config_schema=SlackRetrieverConfig,
    description=SlackRetrieverConfig.Meta.description
)
class SlackRetrieverFactory(BaseFactory[SlackRetrieverConfig, SlackRetriever]):
    def accepts(self, cfg: SlackRetrieverConfig) -> bool:
        return cfg.type == "slack"

    def create(self, cfg: SlackRetrieverConfig, **kwargs: Any) -> SlackRetriever:
        try:
            return SlackRetriever(name=cfg.name,
                                  api_url=cfg.api_url,
                                  top_k_results=cfg.top_k_results,
                                  threshold=cfg.threshold)
        except Exception as e:
            raise PluginConfigurationError(
                f"SlackRetrieverFactory.create() failed: {e}", cfg.dict()
            ) from e
