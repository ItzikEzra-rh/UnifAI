from plugins.base_factory import BaseFactory
from plugins.decorators import register_element
from plugins.exceptions import PluginConfigurationError
from schemas.nodes.base_node import CustomAgentNodeConfig
from nodes.agents.custom_agent_node import CustomAgentNode


@register_element(
    type_key=CustomAgentNodeConfig.Meta.type,
    category=CustomAgentNodeConfig.Meta.category,
    config_schema=CustomAgentNodeConfig,
    description=CustomAgentNodeConfig.Meta.description,
)
class CustomAgentNodeFactory(BaseFactory[CustomAgentNodeConfig, CustomAgentNode]):
    """
    Factory for creating CustomAgentNode instances.
    """

    def accepts(self, cfg: CustomAgentNodeConfig) -> bool:
        return cfg.type == "custom_agent_node"

    def create(self, cfg, **deps):
        try:
            return CustomAgentNode(
                step_ctx=deps.pop("step_ctx"),
                name=cfg.name,
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
