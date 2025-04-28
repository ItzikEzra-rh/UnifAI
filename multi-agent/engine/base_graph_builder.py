from abc import ABC, abstractmethod
from graph.graph_plan import GraphPlan


class BaseGraphBuilder(ABC):
    """
    Abstract interface for any graph execution engine.
    All builders must implement this to translate GraphPlan → executable engine graph.
    """

    @abstractmethod
    def add_node(self, name: str, func):
        """Add a node with a processing function."""
        pass

    @abstractmethod
    def add_edge(self, from_node: str, to_node: str):
        """Add a directed edge from one node to another."""
        pass

    @abstractmethod
    def add_conditional_edge(self, from_node: str, condition_fn, branches: dict):
        """Add conditional edges based on branching logic."""
        pass

    @abstractmethod
    def set_entry_point(self, name: str):
        """Define the graph's entry/start node."""
        pass

    @abstractmethod
    def set_exit_point(self, name: str):
        """Define the graph's exit/end node."""
        pass

    @abstractmethod
    def build(self, plan: GraphPlan):
        """Takes GraphPlan and compiles it to executable graph."""
        pass
