from llms.base_llm import BaseLLM

class LlamaStackLLM(BaseLLM):
    def __init__(self, model_url: str = "http://localhost:8000/v1"):
        self.url = model_url  # Stub for local inference call

    def chat(self, messages: list[dict], stream: bool = False) -> str:
        # In reality: you’d use requests.post() or vLLM client
        return "[LlamaStackLLM] Simulated response to: " + messages[-1]["content"]

    def name(self) -> str:
        return "llamastack"
