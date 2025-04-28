# registry/user_registry.py

from typing import Dict, Any
from registry.element_registry import element_registry

class UserRegistry:
    """
    Per-user/session dynamic registry.
    Builds and holds instantiated LLMs, Tools, Agents, Nodes based on user config.
    """

    def __init__(self):
        # Instantiated objects
        self.llms: Dict[str, Any] = {}
        self.tools: Dict[str, Any] = {}
        self.agents: Dict[str, Any] = {}
        self.nodes: Dict[str, Any] = {}

    # ---- Generic resolver ----

    def instantiate(self, name: str, config_overrides: Dict[str, Any] = None) -> Any:
        """
        Instantiate a component using its registered factory/class.

        Args:
            name: Element name (must have been registered).
            config_overrides: dict with fields to override in schema.

        Returns:
            Instantiated object (Node, Tool, Agent, LLM)
        """
        meta = element_registry.get_metadata(name)
        cls_or_factory = meta["cls"]
        schema_cls = meta["config_schema"]
        element_type = meta["type"]

        # Validate and merge config
        config_data = {}
        if schema_cls:
            config_data = schema_cls(**(config_overrides or {})).dict()

        # Create instance
        if hasattr(cls_or_factory, "create"):   # It's a factory
            instance = cls_or_factory().create(config_data, registry=self)
        else:  # It's a simple static class (like Node)
            instance = cls_or_factory()

        # Save based on type
        if element_type == "llm":
            self.llms[name] = instance
        elif element_type == "tool":
            self.tools[name] = instance
        elif element_type == "agent":
            self.agents[name] = instance
        elif element_type == "node":
            self.nodes[name] = instance
        else:
            raise ValueError(f"Unknown element type: {element_type}")

        return instance

    # --- Typed getters ---

    def get_llm(self, name: str) -> Any:
        return self.llms[name]

    def get_tool(self, name: str) -> Any:
        return self.tools[name]

    def get_agent(self, name: str) -> Any:
        return self.agents[name]

    def get_node(self, name: str) -> Any:
        return self.nodes[name]

    def has_llm(self, name: str) -> bool:
        return name in self.llms

    def has_tool(self, name: str) -> bool:
        return name in self.tools

    def has_agent(self, name: str) -> bool:
        return name in self.agents

    def has_node(self, name: str) -> bool:
        return name in self.nodes
