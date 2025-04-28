from agents.base_agent import BaseAgent


class SlackAgent(BaseAgent):
    def __init__(self, vector_store=None):
        self.vector_store = vector_store or {}

    def get_answer(self, query: str) -> str:
        return f"[SlackAgent] Answer to '{query}' from Slack data."

    def name(self) -> str:
        return "slack_agent"
