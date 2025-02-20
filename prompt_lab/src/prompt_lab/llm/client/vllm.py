from .client import LLMClient
from openai import OpenAI
import requests
import os


class VLLMClient(LLMClient):
    def __init__(self, api_url, model_name, max_context_length):
        super().__init__(api_url, max_context_length)
        self.model_name = model_name
        self.openai_api_key = "EMPTY"
        self.openai_api_base = os.path.join(api_url, "v1")
        self.client = OpenAI(
            api_key=self.openai_api_key,
            base_url=self.openai_api_base
        )

    def send_request(self, prompts, max_tokens=None):
        prompts = [prompts] if not isinstance(prompts, list) else prompts
        stream = self.client.completions.create(
            model=self.model_name,
            prompt=prompts,  # Batch prompts
            max_tokens=max_tokens,
            temperature=0.4,
            top_p=0.8,
            stream=True  # Enable streaming
        )

        return stream

    @staticmethod
    def sort_choices(response):
        """Extracts the assistant’s response text in the order of the 'index' key from a structured API response."""
        choices = sorted(response.get("choices", []), key=lambda choice: choice.get("index", 0))
        return choices
