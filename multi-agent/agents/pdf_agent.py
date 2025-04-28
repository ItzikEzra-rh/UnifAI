from agents.base_agent import BaseAgent

class PDFAgent(BaseAgent):
    def __init__(self, documents=None):
        self.documents = documents or []

    def get_answer(self, query: str) -> str:
        return f"[PDFAgent] Queried PDF and found something about '{query}'"

    def name(self) -> str:
        return "pdf_agent"
