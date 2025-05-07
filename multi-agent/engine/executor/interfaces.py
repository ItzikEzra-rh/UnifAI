from typing import Protocol
from runtime.state.base_state import BaseGraphState


class GraphExecutor(Protocol):
    """
    Anything that can run a compiled graph on an initial state.
    """

    def run(self, initial_state):
        """
        Drive the graph from its entry to its exit and return the final state.
        """
        ...

    def stream(self, initial_state, *args, **kwargs):
        """
        stream the graph’s output to the given stream.
        """
    ...


