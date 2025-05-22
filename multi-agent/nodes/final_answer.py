from nodes.base_node import BaseNode
from graph.step_context import StepContext
from graph.state.graph_state import GraphState


class FinalAnswerNode(BaseNode):
    """
    Picks the best answer already produced by upstream steps and
    stores it under state["final_output"].
    """

    def __init__(self, *, step_ctx: StepContext, name: str = "final_answer"):
        super().__init__(step_ctx=step_ctx, name=name)

    def run(self, state: GraphState) -> GraphState:
        state["final_output"] = state.get("output")
        return state
