from typing import Any, List
from plugins.decorators import register_element
from schemas.nodes.base_node import UserQuestionNodeConfig
from nodes.user_question import UserQuestionNode
from plugins.base_factory import BaseFactory
from plugins.exceptions import PluginConfigurationError


@register_element(
    type_key=UserQuestionNodeConfig.Meta.type,
    category=UserQuestionNodeConfig.Meta.category,
    config_schema=UserQuestionNodeConfig,
    description=UserQuestionNodeConfig.Meta.description,
)
class UserQuestionNodeFactory(BaseFactory[UserQuestionNodeConfig, UserQuestionNode]):
    """
    Factory for creating UserQuestionNode instances.
    """

    def accepts(self, cfg: UserQuestionNodeConfig) -> bool:
        # Only handle configs where type matches our registration key
        return cfg.type == "user_question_node"

    def create(
            self,
            cfg: UserQuestionNodeConfig,
            *,
            llm: Any = None,
            retriever: Any = None,
            tools: List[Any] = None
    ) -> UserQuestionNode:
        """
        Instantiate a UserQuestionNode.

        :param cfg: Merged BaseNodeConfig (with at least .type and .name).
        :param llm:       Unused
        :param retriever: Unused
        :param tools:     Unused
        :raises PluginConfigurationError: if instantiation fails
        """
        try:
            # Use the configured name or fall back to the type
            node_name = cfg.name or cfg.type
            node = UserQuestionNode(name=node_name)
            return node
        except Exception as e:
            raise PluginConfigurationError(
                f"UserQuestionNodeFactory.create failed: {e}",
                cfg.dict()
            ) from e
