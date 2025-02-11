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
    element_type: str
    name: str
    context: str
    question_system_message: str
    seed_system_message: str
    question_seed: str
    question_options: []
    answer: str  # final answer
    question_validation: str
    answer_validation: str
    original_data: dict
    formatted_chat_prompt: str = ""
    question: str = ""  # final question
    validation: str = ""  # validation for the response of the question
    current_system_message: str = ""  # system message for the seed or for the question
    current_question: str = ""  # could change because it could be seed question or the question it self
    current_answer: str = ""  # it could be the question or the answer
    current_validation: str = ""
    token_count: int = 0
    answer_gen_retry_count: int = 0
    question_gen_retry_count: int = 0
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

    def is_question_generation_state(self):
        return self.question_seed and not self.question_options and not self.question

    def is_answer_generation_state(self):
        return bool(self.question or self.question_options) and not self.answer

    def export(self):
        """export format is only question and answer"""
        return {
            "question": self.question,
            "answer": self.answer
        }

    def __repr__(self) -> str:
        return json.dumps(self.to_dict(), indent=2)
