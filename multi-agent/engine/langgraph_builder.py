from typing import Any, Dict, Callable
from typing_extensions import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

from engine.base_graph_builder import BaseGraphBuilder


class LangGraphBuilder(BaseGraphBuilder):
    """
    Concrete GraphBuilder that targets LangGraph’s StateGraph API.
    """

    class State(TypedDict):
        # Example shared state slot for messages
        messages: Annotated[list, add_messages]

    def __init__(self) -> None:
        # initialize an empty StateGraph
        self._graph = StateGraph(self.State)

    def add_node(self, name: str, func: Any) -> None:
        self._graph.add_node(name, func)

    def add_edge(self, from_node: str, to_node: str) -> None:
        self._graph.add_edge(from_node, to_node)

    def add_conditional_edge(
            self,
            from_node: str,
            condition: Callable[[Dict[str, Any]], Any],
            branches: Dict[Any, str]
    ) -> None:
        """
        LangGraph supports conditional edges by providing a `guard` function.
        We wire one edge per branch outcome.
        """
        for outcome, target in branches.items():
            # Each edge carries the same `condition` function; the engine
            # will route to `target` only when `condition(state) == outcome`.
            self._graph.add_edge(
                from_node,
                target,
                condition=condition,
                branch_key=outcome
            )

    def set_entry(self, name: str) -> None:
        self._graph.set_entry_point(name)

    def set_exit(self, name: str) -> None:
        # Allow `name` or explicit END
        self._graph.set_finish_point(name or END)

    def build(self) -> Any:
        """
        Compile the StateGraph into LangGraph’s executable DAG.
        """
        return self._graph.compile()
