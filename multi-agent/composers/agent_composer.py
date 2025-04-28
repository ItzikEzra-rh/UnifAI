# composers/agent_composer.py

from typing import Dict, Any
from agents.base_agent import BaseAgent
from agents.langchain_agent_node import LangChainAgentNode
from schemas.agent_config import AgentConfig
from plugins.exceptions import PluginConfigurationError


class AgentComposer:
    """
    Constructs a dynamic 'custom_agent' node from its config dict.
    """

    @staticmethod
    def build(cfg: Dict[str, Any], registry: PluginRegistry) -> BaseAgent:
        """
        1. Validate cfg via AgentConfig (Pydantic).
        2. Resolve llm, tools, retriever via PluginRegistry.
        3. Instantiate and return a LangChainAgentNode.

        :param cfg: merged config dict (has 'name','llm','tools','retriever','system_message').
        :param registry: PluginRegistry for resolving dependencies.
        :returns: instance of BaseAgent (LangChainAgentNode).
        """
        # 1) Validate config
        try:
            data = AgentConfig(**cfg)
        except Exception as e:
            raise PluginConfigurationError("Invalid agent config", cfg) from e

        # 2) Resolve dependencies
        try:
            llm = registry.get_llm(data.llm)
            tools = [registry.get_tool(t) for t in data.tools]
            retriever = registry.get_retriever(data.retriever)
        except Exception as e:
            raise PluginConfigurationError("Failed to resolve agent dependencies", cfg) from e

        # 3) Instantiate the agent node
        try:
            return LangChainAgentNode(
                name=data.name,
                system_message=data.system_message,
                llm=llm,
                tools=tools,
                retriever=retriever,
            )
        except Exception as e:
            raise PluginConfigurationError("Failed to instantiate agent node", cfg) from e
