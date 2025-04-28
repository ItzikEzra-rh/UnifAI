# plugins/agent_factories/custom_agent_factory.py

from typing import Any, Dict, List
from pydantic import BaseModel, ValidationError, Field
from plugins.base_factory import BaseFactory
from plugins.exceptions import PluginConfigurationError
from plugins.plugin_registry import PluginRegistry
from schemas.agent_config import AgentConfig  # Pydantic schema for agent configs
from agents.base_agent import BaseAgent
from agents.langchain_agent_node import LangChainAgentNode


class CustomAgentFactory(BaseFactory):
    """
    Factory for constructing “custom_agent” nodes:
    an LLM-driven agent with optional tools and a retriever.

    This implements SOLID principles:
      - Single Responsibility: builds one kind of node
      - Open/Closed: to support new agent types, drop in another factory
      - Liskov: adheres to BaseFactory interface
      - Interface Segregation: only accepts & create methods
      - Dependency Inversion: relies on abstract PluginRegistry & BaseAgent
    """

    def accepts(self, cfg: Dict[str, Any]) -> bool:
        """
        Determine if this factory can handle the given config.
        We look for cfg['type'] == 'custom_agent'.
        """
        return cfg.get("type") == "custom_agent"

    def create(self, cfg: Dict[str, Any], registry: PluginRegistry) -> BaseAgent:
        """
        Validate the config and instantiate the agent node.

        :param cfg: Raw config dict (must include 'name', 'type'='custom_agent',
                    'llm', optional 'tools', 'retriever', 'system_message').
        :param registry: PluginRegistry to resolve llm, tools, retriever.
        :returns: An instance of BaseAgent (e.g. LangChainAgentNode).
        :raises PluginConfigurationError: on validation or instantiation errors.
        """
        # 1) Validate & coerce via Pydantic
        try:
            data = AgentConfig(**cfg)
        except ValidationError as ve:
            raise PluginConfigurationError("Invalid CustomAgent config", cfg) from ve

        # 2) Resolve dependencies from the registry
        try:
            # Resolve the LLM client
            llm_client = registry.get_llm(data.llm)

            # Resolve any tool instances
            tools: List[Any] = [
                registry.get_tool(tool_name) for tool_name in data.tools
            ]

            # Resolve the retriever (data source)
            retriever = registry.get_retriever(data.retriever)

        except Exception as e:
            raise PluginConfigurationError(
                f"Failed to resolve dependencies for agent '{data.name}': {e}", cfg
            ) from e

        # 3) Instantiate the agent node
        try:
            agent_node = LangChainAgentNode(
                name=data.name,
                system_message=data.system_message,
                llm=llm_client,
                tools=tools,
                retriever=retriever,
            )
        except Exception as e:
            raise PluginConfigurationError(
                f"Failed to instantiate LangChainAgentNode: {e}", cfg
            ) from e

        return agent_node
