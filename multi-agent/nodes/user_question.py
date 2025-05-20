from nodes.base_node import BaseNode
from graph.state.graph_state import GraphState
from llms.chat.message import ChatMessage, Role


class UserQuestionNode(BaseNode):
    """
    A node that “receives” or displays the user’s input.

    In this simple implementation, it just logs whatever is already stored
    in state["user_input"], then passes the state onward unchanged.
    """

    def __init__(self, name: str = "user_question"):
        # No LLM, retriever, or tools needed here—just call BaseNode with defaults
        super().__init__(name=name)

    def run(self, state: GraphState) -> GraphState:
        """
        Run the node, which simply adds the user input to the chat history and returns the state.
        """
        user_input = state.get("user_prompt", "<no input provided>")
        state["messages"] = [ChatMessage(role=Role.USER, content=user_input)]
        return state
