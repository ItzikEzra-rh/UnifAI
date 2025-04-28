from llms.base_llm import BaseLLM
from langchain.chat_models import ChatOpenAI

class OpenAILLM(BaseLLM):
    def __init__(self, api_key: str, model: str = "gpt-4", temperature=0.7):
        self.client = ChatOpenAI(openai_api_key=api_key, model=model, temperature=temperature)

    def chat(self, messages: list[dict], stream: bool = False) -> str:
        return self.client.invoke(messages)

    def name(self) -> str:
        return "openai"
