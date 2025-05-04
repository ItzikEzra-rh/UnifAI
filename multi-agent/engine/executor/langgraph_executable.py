from typing import Any
from engine.executor.interfaces import GraphExecutor
from runtime.state.base_state import BaseGraphState


class LangGraphExecutor(GraphExecutor):
    """
    Wraps a LangGraph compiled graph (which has .invoke),
    exposing it as a GraphExecutor with .run().
    """

    def __init__(self, compiled_graph: Any) -> None:
        self._compiled = compiled_graph

    def run(self, initial_state: BaseGraphState) -> BaseGraphState:
        # delegate to LangGraph’s invoke API
        return self._compiled.invoke(initial_state)
