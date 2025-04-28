class FinalAnswerNode:
    def __call__(self, state):
        result = state.get("critic_judgement") or state.get("discussion_answer")
        state["final_output"] = result
        print("Final output:\n", result)
        return state
