from plugins.decorators import register_element
from plugins.base_factory import BaseFactory
from plugins.exceptions import PluginConfigurationError
from nodes.models.base_node import FinalAnswerNodeConfig
from nodes.final_answer import FinalAnswerNode


@register_element(
    type_key=FinalAnswerNodeConfig.Meta.type,
    category=FinalAnswerNodeConfig.Meta.category,
    config_schema=FinalAnswerNodeConfig,
    description=FinalAnswerNodeConfig.Meta.description,
)
class FinalAnswerNodeFactory(BaseFactory[FinalAnswerNodeConfig, FinalAnswerNode]):
    """Builds a FinalAnswerNode (no LLM / retriever / tools needed)."""

    def accepts(self, cfg: FinalAnswerNodeConfig) -> bool:
        return cfg.type == "final_answer_node"

    def create(self, cfg: FinalAnswerNodeConfig, **deps) -> FinalAnswerNode:
        try:
            return FinalAnswerNode(
                name=cfg.name or cfg.type
            )
        except Exception as exc:
            raise PluginConfigurationError(
                f"FinalAnswerNodeFactory.create failed: {exc}",
                cfg.dict()
            ) from exc
