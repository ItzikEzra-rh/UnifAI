from typing import Any, Dict, Literal
from pydantic import BaseModel, ValidationError, Field
from plugins.base_factory import BaseFactory
from plugins.exceptions import PluginConfigurationError
from agents.jira_agent import JiraAgent


# class JiraRetrieverConfig(BaseModel):
#     """
#     Configuration schema for the Jira retriever.
#     """
#     name: str
#     type: Literal["jira"] = Field("jira", const=True)
#     vector_store: Dict[str, Any] = {}  # Vector store settings for RAG
#

class JiraRetrieverFactory(BaseFactory):
    """
    Factory for constructing Jira-based retrievers.
    Loads JiraAgent instances configured with vector stores.
    """

    def accepts(self, cfg: Dict[str, Any]) -> bool:
        """
        Returns True if this factory can handle the given config.
        """
        return cfg.get("type") == "jira"

    def create(self, cfg: Dict[str, Any]) -> JiraAgent:
        """
        Validate config and instantiate a JiraAgent.

        :param cfg: Raw config dict with keys 'name', 'type', 'vector_store'.
        :raises PluginConfigurationError: on validation or instantiation failure.
        :return: JiraAgent instance.
        """
        # 1. Validate config via Pydantic
        try:
            data = JiraRetrieverConfig(**cfg)
        except ValidationError as ve:
            raise PluginConfigurationError("Invalid Jira retriever config", cfg) from ve

        # 2. Instantiate the agent
        try:
            agent = JiraAgent(vector_store=data.vector_store)
        except Exception as e:
            raise PluginConfigurationError(f"Failed to create JiraAgent: {e}", cfg) from e

        return agent
