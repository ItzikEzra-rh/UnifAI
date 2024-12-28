# my_project/models/prompt.py

import json

class Prompt:
    """
    Represents a single prompt with:
      - UUID
      - The final 'formatted_prompt' text to be sent to LLM
      - Token count
      - Arbitrary 'metadata' dict with details about the prompt
    """

    def __init__(self, uuid: str, formatted_prompt: str, metadata: dict, token_count: int = 0):
        self.uuid = uuid
        self.formatted_prompt = formatted_prompt
        self.metadata = metadata or {}
        self.token_count = token_count

    def to_dict(self) -> dict:
        """
        Convert to a dictionary for serialization (e.g., sending to Celery).
        """
        return {
            "uuid": self.uuid,
            "formatted_prompt": self.formatted_prompt,
            "token_count": self.token_count,
            "metadata": self.metadata
        }

    def __repr__(self) -> str:
        return json.dumps(self.to_dict(), indent=2)
