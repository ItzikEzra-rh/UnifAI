import json


class Prompt:
    """
    Represents a single prompt with:
      - UUID
      - The final 'formatted_prompt' text to be sent to LLM
      - Token count
      - Arbitrary 'metadata' dict with details about the prompt
    """

    def __init__(self, uuid: str, formatted_prompt: str, metadata: dict, token_count: int = 0, retry_count: int = 0,
                 failed: bool = False):
        self.uuid = uuid
        self.formatted_prompt = formatted_prompt
        self.metadata = metadata or {}
        self.token_count = token_count
        self.retry_count = retry_count
        self.failed = failed
        self.skip_reason = None

    def set_skip_reason(self, reason: str) -> None:
        self.skip_reason = reason

    def set_output_text(self, output_text: str) -> None:
        self.metadata["output_text"] = output_text

    @property
    def is_failed(self) -> bool:
        return self.failed

    def to_dict(self) -> dict:
        """
        Convert to a dictionary for serialization (e.g., sending to Celery).
        """
        return {
            "uuid": self.uuid,
            "formatted_prompt": self.formatted_prompt,
            "token_count": self.token_count,
            "metadata": self.metadata,
            "retry_count": self.retry_count,
            "failed": self.failed,
            "skip_reason": self.skip_reason
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Prompt":
        """
        Create a Prompt instance from a dictionary.
        """
        return cls(
            uuid=data.get("uuid", ""),
            formatted_prompt=data.get("formatted_prompt", ""),
            metadata=data.get("metadata", {}),
            token_count=data.get("token_count", 0),
            retry_count=data.get("retry_count", 0),
            failed=data.get("failed", 0),
        )

    def __repr__(self) -> str:
        return json.dumps(self.to_dict(), indent=2)
