import random
from .prompt_policy import PromptPolicy
from ..prompt import Prompt
from prompt_lab.utils import logger


class PromptPassPolicy(PromptPolicy):
    """
    If 'retry_count' < max_retries, increment it and allow re-queue.
    Otherwise mark as skipped.
    """

    def apply(self, prompt: Prompt) -> bool:
        """Apply a retry policy for prompts in question/answer generation states."""

        if not prompt.is_review_failed and not prompt.failed and prompt.is_answer_generation_state():
            prompt.question = prompt.current_question
            prompt.answer = prompt.current_answer
            print("PromptPassPolicy succeeded")
            return True
        print("PromptPassPolicy failed")
        return False
