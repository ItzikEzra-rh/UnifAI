from plugins.base_factory import BaseFactory
from plugins.decorators import register_element
from plugins.exceptions import PluginConfigurationError
from schemas.nodes.base_node import MockAgentNodeConfig
from nodes.agents.mock_agent import MockAgentNode


@register_element(
    type_key=MockAgentNodeConfig.Meta.type,
    category=MockAgentNodeConfig.Meta.category,
    config_schema=MockAgentNodeConfig,
    description=MockAgentNodeConfig.Meta.description,
)
class MockAgentNodeFactory(BaseFactory[MockAgentNodeConfig, MockAgentNode]):
    """Factory for MockAgentNode (needs no LLM / retriever / tools)."""

    def accepts(self, cfg: MockAgentNodeConfig) -> bool:
        return cfg.type == "mock_agent_node"

    def create(self, cfg: MockAgentNodeConfig, **deps) -> MockAgentNode:
        """
        deps delivers at least:
          • step_ctx  – mandatory identity capsule
          • llm / retriever / tools – ignored by this node
        """
        try:
            return MockAgentNode(
                step_ctx=deps.pop("step_ctx"),
                name=cfg.name or cfg.type,
                fixed_message=getattr(cfg, "fixed_message", None)
            )
        except Exception as exc:
            raise PluginConfigurationError(
                f"MockAgentNodeFactory.create failed: {exc}",
                cfg.dict()
            ) from exc
