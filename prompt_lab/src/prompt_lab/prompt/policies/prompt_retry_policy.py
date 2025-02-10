import random
from .prompt_policy import PromptPolicy
from ..prompt import Prompt
from prompt_lab.utils import logger


class PromptRetryPolicy(PromptPolicy):
    """
    If 'retry_count' < max_retries, increment it and allow re-queue.
    Otherwise mark as skipped.
    """

    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries

    def apply(self, prompt: Prompt) -> bool:
        """Apply a retry policy for prompts in question/answer generation states."""

        # Only proceed if the review has failed
        if not prompt.is_review_failed:
            return False

        # Handle question generation retry
        if prompt.is_question_generation_state():
            prompt.question_gen_retry_count += 1
            if prompt.question_options:
                prompt.current_question = random.choice(prompt.question_options)
            logger.info(
                f"[RetryPolicy] Retrying prompt {prompt.uuid} - "
                f"question generation retry (attempt {prompt.question_gen_retry_count}/{self.max_retries})"
            )
            return True

        # Handle answer generation retry
        if prompt.is_answer_generation_state():
            prompt.answer_gen_retry_count += 1
            logger.info(
                f"[RetryPolicy] Retrying prompt {prompt.uuid} - "
                f"answer generation retry (attempt {prompt.answer_gen_retry_count}/{self.max_retries})"
            )
            return True

        return False
