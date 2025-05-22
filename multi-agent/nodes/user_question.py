from nodes.base_node import BaseNode
from graph.step_context import StepContext
from graph.state.graph_state import GraphState
from llms.chat.message import ChatMessage, Role


class UserQuestionNode(BaseNode):
    """
    Injects the raw user prompt into the chat history.
    """

    def __init__(self,
                 *,
                 step_ctx: StepContext,
                 name: str = "user_question",
                 **kwargs):
        super().__init__(step_ctx=step_ctx, name=name, **kwargs)

    def run(self, state: GraphState) -> GraphState:
        prompt = state.get("user_prompt", "<no input>")
        state["messages"] = [ChatMessage(role=Role.USER, content=prompt)]
        return state
