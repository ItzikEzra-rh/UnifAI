from elements.common.base_factory import BaseFactory
from elements.common.exceptions import PluginConfigurationError
from .config import CustomAgentNodeConfig
from .custom_agent import CustomAgentNode


class CustomAgentNodeFactory(BaseFactory[CustomAgentNodeConfig, CustomAgentNode]):
    """
    Factory for creating CustomAgentNode instances.
    """

    def accepts(self, cfg: CustomAgentNodeConfig, element_type: str) -> bool:
        return element_type == "custom_agent_node"

    def create(self, cfg, **deps):
        try:
            return CustomAgentNode(
                llm=deps.pop("llm"),
                retriever=deps.pop("retriever"),
                tools=deps.pop("tools"),
                system_message=cfg.system_message,
                retries=cfg.retries,
            )
        except Exception as e:
            raise PluginConfigurationError(
                f"CustomAgentNodeFactory.create failed: {e}",
                cfg.dict()
            ) from e
