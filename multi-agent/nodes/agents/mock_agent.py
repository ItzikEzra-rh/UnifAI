from typing import Any, Dict
from nodes.base_node import BaseNode
from runtime.state.graph_state import GraphState


class MockAgentNode(BaseNode):
    """
    A simple “mock” agent node for testing or dry-run purposes.

    Behavior:
      - If `system_message` is provided, uses that as the fixed response.
      - Otherwise, echoes back the user’s input.
      - Always writes its reply into state["output"].
    """

    def __init__(self, name: str = "mock_agent"):
        # No LLM, retriever, or tools needed here—just call BaseNode with defaults
        super().__init__(name=name)

    def run(self, state: dict) -> dict:
        """
        Perform the mock node’s logic.

        Args:
            state: the current graph state, expected to contain state["input"].

        Returns:
            Updated state with state["output"] set.
        """
        # Use configured system_message as the mock reply if set
        if self.system_message:
            response = self.system_message
        else:
            # Fallback: echo the user’s last input
            user_input = state.get("input", "")
            response = f"MockAgentNode echo: {user_input}"

        # Place the result in the state for downstream nodes
        state["output"] = response
        return state
