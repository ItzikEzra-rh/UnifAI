from plugins.base_factory import BaseFactory
from plugins.decorators import register_element
from plugins.exceptions import PluginConfigurationError
from nodes.models.base_node import MergerLLMNodeConfig
from nodes.llm_merger import LLMMergerNode


@register_element(
    type_key=MergerLLMNodeConfig.Meta.type,
    category=MergerLLMNodeConfig.Meta.category,
    config_schema=MergerLLMNodeConfig,
    description=MergerLLMNodeConfig.Meta.description,
)
class LLMMergerNodeFactory(BaseFactory[MergerLLMNodeConfig, LLMMergerNode]):
    """Factory for LLMMergerNode."""

    def accepts(self, cfg: MergerLLMNodeConfig) -> bool:
        return cfg.type == "merger_node"

    def create(self, cfg: MergerLLMNodeConfig, **deps) -> LLMMergerNode:
        try:
            return LLMMergerNode(
                llm=deps.pop("llm"),
                name=cfg.name or cfg.type,
                system_message=cfg.system_message,
                retries=cfg.retries,
            )
        except Exception as exc:
            raise PluginConfigurationError(
                f"LLMMergerNodeFactory.create failed: {exc}",
                cfg.dict()
            ) from exc
