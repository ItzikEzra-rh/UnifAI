from abc import ABC, abstractmethod

class BaseNode(ABC):
    """
    Interface for all executable nodes in the graph.
    """

    @abstractmethod
    def __call__(self, state: dict) -> dict:
        """
        Receives graph state, returns new state dict.
        """
        pass
