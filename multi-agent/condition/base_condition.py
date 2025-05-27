from abc import ABC, abstractmethod
from typing import Any, Dict
from runtime.state.graph_state import GraphState


class BaseCondition(ABC):
    """
    All conditions must implement __call__(state) -> Any.
    The return value is matched against branches in the graph.
    """

    @abstractmethod
    def __call__(self, state: dict) -> Any:
        """
        Evaluate the condition against the provided graph `state`.
        Return a key that will select the next branch.
        """
        ...
