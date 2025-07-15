from elements.common.base_factory import BaseFactory
from elements.common.exceptions import PluginConfigurationError
from .config import FinalAnswerNodeConfig
from .final_answer import FinalAnswerNode


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
