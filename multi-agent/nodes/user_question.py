from typing import Any, Dict, List
from nodes.base_node import BaseNode


class UserQuestionNode(BaseNode):
    """
    A node that “receives” or displays the user’s input.

    In this simple implementation, it just logs whatever is already stored
    in state["user_input"], then passes the state onward unchanged.
    """

    def __init__(self, name: str = "user_question"):
        # No LLM, retriever, or tools needed here—just call BaseNode with defaults
        super().__init__(name=name)

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Log the incoming user_input and return the unmodified state.
        Downstream nodes can read state["user_input"].
        """
        user_input = state.get("input", "<no input provided>")
        print(f"UserQuestionNode: Prompt received: {user_input}")
        return state
