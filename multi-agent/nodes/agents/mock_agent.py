from nodes.base_node import BaseNode
from graph.step_context import StepContext
from graph.state.graph_state import GraphState
from typing import Optional


class MockAgentNode(BaseNode):
    """
    Test stub: echoes the user prompt or returns a fixed message.
    """

    def __init__(self,
                 *,
                 step_ctx: StepContext,
                 name: str = "mock_agent",
                 fixed_message: Optional[str] = None):
        super().__init__(step_ctx=step_ctx, name=name)
        self.fixed_message = fixed_message

    def run(self, state: GraphState) -> GraphState:
        response = (self.fixed_message
                    if self.fixed_message is not None
                    else f"Mock echo: {state.get('input', '')}")
        state["output"] = response
        return state
