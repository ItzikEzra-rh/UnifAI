from prompt_lab.llm_client.client import LLMClient
import requests


class VLLMClient(LLMClient):
    def __init__(self, api_url, model_name, max_context_length):
        super().__init__(api_url, max_context_length)
        self.model_name = model_name

    def send_request(self, prompts, max_tokens=None):
        # Format prompts with tokenizer utility
        prompts = [prompts] if not isinstance(prompts, list) else prompts

        # Prepare data for vllm
        data = {
            "model": self.model_name,
            "prompt": prompts,
            "max_tokens": max_tokens,
            "temperature": 0.3,
            "frequency_penalty": 0.6,
            "presence_penalty": 0.4
        }
        # Send request
        response = requests.post(self.api_url, json=data, headers={"Content-Type": "application/json"})
        response.raise_for_status()

        # Extract responses in order
        return self.sort_choices(response.json())

    @staticmethod
    def sort_choices(response):
        """Extracts the assistant’s response text in the order of the 'index' key from a structured API response."""
        choices = sorted(response.get("choices", []), key=lambda choice: choice.get("index", 0))
        return choices
