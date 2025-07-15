from elements.nodes.common.base_node import BaseNode
from graph.state.graph_state import GraphState
from typing import Optional


class MockAgentNode(BaseNode):
    """
    Test stub: echoes the user prompt or returns a fixed message.
    """

    def __init__(self,
                 *,
                 name: str = "mock_agent",
                 fixed_message: Optional[str] = None,
                 **kwargs):
        super().__init__(name=name, **kwargs)
        self.fixed_message = fixed_message

    def run(self, state: GraphState) -> GraphState:
        response = (self.fixed_message
                    if self.fixed_message is not None
                    else f"Mock echo: {state.get('input', '')}")
        state["output"] = response
        return state
