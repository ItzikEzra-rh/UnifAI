from elements.common.base_factory import BaseFactory
from elements.common.exceptions import PluginConfigurationError
from .config import MockAgentNodeConfig
from .mock_agent import MockAgentNode


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
                name=cfg.name or cfg.type,
                fixed_message=getattr(cfg, "fixed_message", None)
            )
        except Exception as exc:
            raise PluginConfigurationError(
                f"MockAgentNodeFactory.create failed: {exc}",
                cfg.dict()
            ) from exc
