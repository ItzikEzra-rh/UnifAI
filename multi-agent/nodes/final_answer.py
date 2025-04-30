from typing import Any, Dict, List
from nodes.base_node import BaseNode


class FinalAnswerNode(BaseNode):
    """
    A node that picks the best answer from prior steps (critic or discussion)
    and writes it into state["final_output"], then prints it.
    """

    def __init__(self, name: str = "final_answer"):
        # No LLM, retriever, or tools needed for finalization
        super().__init__(name=name)

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Selects the final answer and emits it.
        """
        # Prefer the critic's judgement if present; otherwise use the discussion result
        result = state.get("critic_judgement") or state.get("discussion_answer")
        state["final_output"] = result

        # Print or otherwise emit the final output
        print("FinalAnswerNode: Final output:\n", result)
        return state
