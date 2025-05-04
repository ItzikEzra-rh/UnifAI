# multi_agent/engine/graph_builder_factory.py

from typing import Dict, Type
from engine.builder.base_graph_builder import BaseGraphBuilder
from engine.builder.langgraph_builder import LangGraphBuilder
from runtime.state.base_state import BaseGraphState


class GraphBuilderFactory:
    """
    Factory for creating graph execution engine builders (e.g., LangGraphBuilder).
    You inject the state class once, and every builder gets it.
    """

    def __init__(self, state_cls: Type[BaseGraphState]) -> None:
        # store the injected state implementation
        self._state_cls = state_cls

        # registry of builder classes (each must accept state_cls in their __init__)
        self._registry: Dict[str, Type[BaseGraphBuilder]] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        # register your default builders here
        self.register("langgraph", LangGraphBuilder)

    def register(self, key: str, builder_cls: Type[BaseGraphBuilder]) -> None:
        """
        Register a new graph builder type.

        Args:
            key: Unique identifier (e.g. "langgraph")
            builder_cls: A subclass of BaseGraphBuilder whose __init__ signature is
                         def __init__(self, state_cls: Type[StateProtocol]) -> None
        """
        if not issubclass(builder_cls, BaseGraphBuilder):
            raise TypeError(f"{builder_cls} must inherit from BaseGraphBuilder")
        self._registry[key] = builder_cls

    def create(self, key: str) -> BaseGraphBuilder:
        """
        Instantiate the builder by key, injecting the state class.

        Args:
            key: One of the registered builder names

        Returns:
            An instance of BaseGraphBuilder
        """
        if key not in self._registry:
            raise ValueError(f"Unknown graph builder type: {key}")
        builder_cls = self._registry[key]
        return builder_cls(self._state_cls)
