from typing import List
from prompt_lab.prompt import Prompt
from .batch_strategy import BatchStrategy
from prompt_lab.utils import logger


class AnswerGenerationStateStrategy(BatchStrategy):
    """
    """

    def apply(self, current_batch: List[Prompt], new_prompt: Prompt) -> bool:
        answer_generation_prompts = all(
            not prompt.failed and prompt.is_answer_generation_state() for prompt in current_batch)

        if answer_generation_prompts and not new_prompt.failed and new_prompt.is_answer_generation_state():
            return True
        return False

    @property
    def blocker(self) -> bool:
        """Indicates whether the strategy is a blocker."""
        return False
