from abc import ABC, abstractmethod
from typing import Any, Dict, List
from runtime.state.graph_state import GraphState


class BaseNode(ABC):
    """
    All graph nodes follow this interface.
    Concrete nodes are instantiated with fully-resolved dependencies.
    """

    def __init__(
            self,
            name: str,
            llm: Any = None,
            retriever: Any = None,
            tools: List[Any] = (),
            system_message: str = "",
            retries: int = 1
    ):
        self.name = name
        self.llm = llm
        self.retriever = retriever
        self.tools = list(tools)
        self.system_message = system_message or ""
        self.retries = max(1, retries)

    @abstractmethod
    def run(self, state: dict) -> dict:
        """
        Perform this node’s logic, returning an updated state dict.
        Called by the graph executor.
        """
        ...

    def __call__(self, state: dict) -> dict:
        return self.run(state)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name!r}>"
