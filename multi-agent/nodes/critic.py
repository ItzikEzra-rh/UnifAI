class CriticNode:
    def __init__(self, llm):
        self.llm = llm

    def __call__(self, state):
        msg = [{"role": "user", "content": f"Please verify this answer:\n{state['discussion_answer']}"}]
        verified = self.llm.chat(msg)
        state["critic_judgement"] = verified
        return state
