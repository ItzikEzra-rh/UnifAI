from typing import Any, List
from plugins.decorators import register_element
from schemas.nodes.base_node import FinalAnswerNodeConfig
from nodes.final_answer import FinalAnswerNode
from plugins.base_factory import BaseFactory
from plugins.exceptions import PluginConfigurationError


@register_element(
    type_key=FinalAnswerNodeConfig.Meta.type,
    category=FinalAnswerNodeConfig.Meta.category,
    config_schema=FinalAnswerNodeConfig,
    description=FinalAnswerNodeConfig.Meta.description,
)
class FinalAnswerNodeFactory(BaseFactory[FinalAnswerNodeConfig, FinalAnswerNode]):
    """
    Factory for creating FinalAnswerNode instances.
    """

    def accepts(self, cfg: FinalAnswerNodeConfig) -> bool:
        return cfg.type == "final_answer_node"

    def create(
            self,
            cfg: FinalAnswerNodeConfig,
            *,
            llm: Any = None,
            retriever: Any = None,
            tools: List[Any] = None
    ) -> FinalAnswerNode:
        """
        Instantiate a FinalAnswerNode.

        :param cfg: Merged BaseNodeConfig (with .type, .name).
        :param llm:       Unused
        :param retriever: Unused
        :param tools:     Unused
        :raises PluginConfigurationError: if instantiation fails
        """
        try:
            node_name = cfg.name or cfg.type
            node = FinalAnswerNode(name=node_name)
            return node
        except Exception as e:
            raise PluginConfigurationError(
                f"FinalAnswerNodeFactory.create failed: {e}",
                cfg.dict()
            ) from e
