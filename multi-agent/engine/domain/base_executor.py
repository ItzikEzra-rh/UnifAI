from abc import ABC, abstractmethod
from typing import Any, Iterator
from graph.state.graph_state import GraphState


class BaseGraphExecutor(ABC):
    """
    Abstract base class for graph executors.

    Every engine implementation (LangGraph, Temporal, etc.)
    must subclass this and implement all three methods.
    """

    @abstractmethod
    def run(self, initial_state: Any) -> Any:
        """
        Drive the graph from its entry to its exit and return the final state.
        """
        ...

    @abstractmethod
    def stream(self, initial_state: Any, *args, **kwargs) -> Iterator[Any]:
        """
        Stream the graph's output chunk by chunk.
        """
        ...

    @abstractmethod
    def get_state(self) -> Any:
        """
        Get the current state of the graph.
        """
        ...
