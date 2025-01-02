import random
from dataclasses import dataclass, asdict
import json


@dataclass
class Prompt:
    """
    Represents a single prompt with:
      - A unique identifier (UUID)
      - The formatted prompt text to be sent to the LLM
      - The type of element (element_type) being represented
      - Group and category classifications
      - Validation rules as a dictionary
      - Input text associated with the prompt
      - Original data used for generating the prompt
      - Token count and retry count for managing processing
      - Flags indicating whether the prompt failed and the reason for skipping
    """
    uuid: str
    formatted_prompt: str
    element_type: str
    group: str
    category: str
    questions: list
    validation: dict
    input_text: str
    original_data: dict
    output_text: str = ""
    token_count: int = 0
    retry_count: int = 0
    failed: bool = False
    review_failed: bool = False
    fail_reason: str = None

    def set_fail_reason(self, reason: str) -> None:
        self.fail_reason = reason

    @property
    def is_failed(self) -> bool:
        return self.failed

    @property
    def is_review_failed(self) -> bool:
        return self.review_failed

    def to_dict(self) -> dict:
        """
        Convert the object to a dictionary for serialization.
        """
        return asdict(self)

    @classmethod
    def from_dict(cls, **kwargs) -> "Prompt":
        """
        Create a Prompt instance from a dictionary.
        """
        return cls(**kwargs)

    def shuffle_user_input(self):
        question = random.choice(self.questions)
        self.input_text = question["question"]
        self.validation = question["validation"]

    def __repr__(self) -> str:
        return json.dumps(self.to_dict(), indent=2)
