from plugins.base_factory import BaseFactory
from plugins.decorators import register_element
from plugins.exceptions import PluginConfigurationError
from schemas.nodes.base_node import MergerLLMNodeConfig
from nodes.llm_merger import LLMMergerNode


@register_element(
    type_key=MergerLLMNodeConfig.model_fields["type"].default,
    category="node",
    config_schema=MergerLLMNodeConfig,
    description="MergerLLMNodeConfig is a configuration schema for the Merger LLM node. "
)
class CustomAgentNodeFactory(BaseFactory[MergerLLMNodeConfig, LLMMergerNode]):
    """
    Factory for creating CustomAgentNode instances.
    """

    def accepts(self, cfg: MergerLLMNodeConfig) -> bool:
        return cfg.type == "merger_node"

    def create(self,
               cfg: MergerLLMNodeConfig,
               *,
               llm=None,
               retriever=None,
               tools=None
               ) -> LLMMergerNode:
        try:
            node = LLMMergerNode(
                name=cfg.name,
                llm=llm,
                system_message=cfg.system_message,
                retries=cfg.retries
            )
            return node
        except Exception as e:
            raise PluginConfigurationError(
                f"CustomAgentNodeFactory.create failed: {e}",
                cfg.dict()
            ) from e
