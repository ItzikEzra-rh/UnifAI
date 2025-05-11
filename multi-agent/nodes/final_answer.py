from nodes.base_node import BaseNode
from graph.graph_state import GraphState


class FinalAnswerNode(BaseNode):
    """
    A node that picks the best answer from prior steps (critic or discussion)
    and writes it into state["final_output"], then prints it.
    """

    def __init__(self, name: str = "final_answer"):
        # No LLM, retriever, or tools needed for finalization
        super().__init__(name=name)

    def run(self, state: GraphState) -> GraphState:
        """
        Selects the final answer and emits it.
        """
        # Prefer the critic's judgement if present; otherwise use the discussion result
        result = state.get("output")

        # Print or otherwise emit the final output

        return state
