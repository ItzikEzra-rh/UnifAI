from llms.base_llm import BaseLLM
# from registry import element_registry


# @element_registry.register_llm("mock_llm")
class MockLLM(BaseLLM):
    def chat(self, messages: list[dict], stream: bool = False) -> str:
        return "[MOCK RESPONSE] Hello! You said: " + messages[-1]["content"]

    def name(self) -> str:
        return "mock"
