from typing import Any, List
from plugins.decorators import register_element
from schemas.nodes.base_node import MockAgentNodeConfig
from nodes.agents.mock_agent import MockAgentNode
from plugins.base_factory import BaseFactory
from plugins.exceptions import PluginConfigurationError


@register_element(
    type_key=MockAgentNodeConfig.type,
    category="node",
    config_schema=MockAgentNodeConfig,
    description="MockAgentNodeConfig"
)
class MockAgentNodeFactory(BaseFactory[MockAgentNodeConfig, MockAgentNode]):
    """
    Factory for creating MockAgentNode instances.

    Delegates dependency resolution to NodeFactory; here we only
    consume the merged BaseNodeConfig and any injected deps.
    """

    def accepts(self, cfg: MockAgentNodeConfig) -> bool:
        # Only accept configs whose `type` matches our registration key
        return cfg.type == "mock_agent_node"

    def create(
            self,
            cfg: MockAgentNodeConfig,
            *,
            llm: Any = None,  # ignored by mock node
            retriever: Any = None,  # ignored by mock node
            tools: List[Any] = None
    ) -> MockAgentNode:
        """
        Build a MockAgentNode from the merged BaseNodeConfig.

        :param cfg: Fully merged BaseNodeConfig with fields:
            - name
            - type == "mock_agent_node"
            - system_message (optional)
            - retries (optional)
        :param llm:       (injected, not used)
        :param retriever: (injected, not used)
        :param tools:     (injected, not used)
        :raises PluginConfigurationError: on instantiation failure
        """
        try:
            node = MockAgentNode(name=cfg.name or "mock_agent_node")
            node.system_message = cfg.system_message or ""
            node.retries = cfg.retries
            return node
        except Exception as e:
            raise PluginConfigurationError(
                f"MockAgentNodeFactory.create failed: {e}",
                cfg.dict()
            ) from e
