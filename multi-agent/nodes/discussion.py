class DiscussionNode:
    def __init__(self, llm):
        self.llm = llm

    def __call__(self, state):
        messages = [{"role": "user", "content": f"Here are agent opinions:\n{state['aggregated_answer']}"}]
        answer = self.llm.chat(messages)
        state["discussion_answer"] = answer
        return state
