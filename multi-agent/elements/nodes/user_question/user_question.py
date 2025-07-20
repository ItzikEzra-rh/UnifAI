from elements.nodes.common.base_node import BaseNode
from graph.state.graph_state import GraphState
from elements.llms.common.chat.message import ChatMessage, Role


class UserQuestionNode(BaseNode):
    """
    Injects the raw user prompt into the chat history.
    """

    def __init__(self,
                 *,
                 name: str = "user_question",
                 **kwargs):
        super().__init__(**kwargs)
        self.name = name

    def run(self, state: GraphState) -> GraphState:
        prompt = state.get("user_prompt", "<no input>")
        state["messages"] = [ChatMessage(role=Role.USER, content=prompt)]
        return state
