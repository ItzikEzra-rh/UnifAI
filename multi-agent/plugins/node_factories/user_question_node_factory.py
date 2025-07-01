from plugins.base_factory import BaseFactory
from plugins.decorators import register_element
from plugins.exceptions import PluginConfigurationError
from nodes.models.base_node import UserQuestionNodeConfig
from nodes.user_question import UserQuestionNode


@register_element(
    type_key=UserQuestionNodeConfig.Meta.type,
    category=UserQuestionNodeConfig.Meta.category,
    config_schema=UserQuestionNodeConfig,
    description=UserQuestionNodeConfig.Meta.description,
)
class UserQuestionNodeFactory(BaseFactory[UserQuestionNodeConfig, UserQuestionNode]):
    """Factory for UserQuestionNode (needs no LLM/retriever/tools)."""

    def accepts(self, cfg: UserQuestionNodeConfig) -> bool:
        return cfg.type == "user_question_node"

    def create(self, cfg: UserQuestionNodeConfig, **deps) -> UserQuestionNode:
        try:
            return UserQuestionNode(
                name=cfg.name or cfg.type
            )
        except Exception as exc:
            raise PluginConfigurationError(
                f"UserQuestionNodeFactory.create failed: {exc}",
                cfg.dict()
            ) from exc
