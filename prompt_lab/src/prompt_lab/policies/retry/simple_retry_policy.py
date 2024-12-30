from .retry_policy import RetryPolicy
from prompt import Prompt
from prompt import PromptGenerator


class SimpleRetryPolicy(RetryPolicy):
    """
    If 'retry_count' < max_retries, increment it and allow re-queue.
    Otherwise mark as skipped.
    """

    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries

    def apply_retry_logic(self, prompt: Prompt) -> bool:
        if prompt.retry_count < self.max_retries:
            prompt.retry_count += 1

            print(f"[RetryPolicy] Retrying prompt {prompt.uuid} (attempt {prompt.retry_count})")
            return True
        else:
            return False
