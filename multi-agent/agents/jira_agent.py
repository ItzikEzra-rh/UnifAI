from agents.base_agent import BaseAgent

class JiraAgent(BaseAgent):
    def __init__(self, vector_store=None):
        self.vector_store = vector_store or {}

    def get_answer(self, query: str) -> str:
        return f"[JiraAgent] Found related issues to '{query}'"

    def name(self) -> str:
        return "jira_agent"
