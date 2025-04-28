# registry/session_registry.py

from typing import Any, Dict


class SessionRegistry:
    """
    Per-session store for all instantiated components:
      - llms
      - tools
      - retrievers
      - agents
      - nodes (optional, if you want to cache Node instances)
    """

    def __init__(self) -> None:
        self._llms: Dict[str, Any] = {}
        self._tools: Dict[str, Any] = {}
        self._retrievers: Dict[str, Any] = {}
        self._agents: Dict[str, Any] = {}
        self._nodes: Dict[str, Any] = {}

    # ---- LLMs ----
    def register_llm(self, name: str, instance: Any) -> None:
        self._llms[name] = instance

    def get_llm(self, name: str) -> Any:
        return self._llms[name]

    # ---- Tools ----
    def register_tool(self, name: str, instance: Any) -> None:
        self._tools[name] = instance

    def get_tool(self, name: str) -> Any:
        return self._tools[name]

    # ---- Retrievers ----
    def register_retriever(self, name: str, instance: Any) -> None:
        self._retrievers[name] = instance

    def get_retriever(self, name: str) -> Any:
        return self._retrievers[name]

    # ---- Agents ----
    def register_agent(self, name: str, instance: Any) -> None:
        self._agents[name] = instance

    def get_agent(self, name: str) -> Any:
        return self._agents[name]

    # ---- (Optional) Nodes ----
    def register_node(self, name: str, instance: Any) -> None:
        self._nodes[name] = instance

    def get_node(self, name: str) -> Any:
        return self._nodes[name]
