from typing import Type, Callable, TypedDict
from langgraph.graph import StateGraph, END
from .base_graph_builder import BaseGraphBuilder
from graph.state.graph_state import GraphState
from engine.executor.langgraph_executable import LangGraphExecutor

from typing import Any, Dict


class LangGraphBuilder(BaseGraphBuilder):
    """
    Concrete GraphBuilder that targets LangGraph’s StateGraph API.
    """

    def __init__(self, state_cls: GraphState) -> None:
        self._graph = StateGraph(state_cls)

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
        self._graph.add_conditional_edges(
            from_node,
            condition,
            branches
        )

    def set_entry(self, name: str) -> None:
        self._graph.set_entry_point(name)

    def set_exit(self, name: str) -> None:
        # Allow `name` or explicit END
        self._graph.set_finish_point(name or END)

    def build_executor(self) -> LangGraphExecutor:
        """
        Compile the StateGraph into LangGraph’s executable.
        """
        return LangGraphExecutor(self._graph.compile())
