import requests
from abc import ABC, abstractmethod


class LLMClient(ABC):
    def __init__(self, api_url, max_context_length):
        self.api_url = api_url
        self.max_context_length = max_context_length

    @abstractmethod
    def send_request(self, prompts, max_tokens=None):
        """Send a request to the LLM API with prompts and receive a response."""
        pass
