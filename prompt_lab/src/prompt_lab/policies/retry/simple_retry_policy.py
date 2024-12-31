from .retry_policy import RetryPolicy
from prompt import Prompt


class SimpleRetryPolicy(RetryPolicy):
    """
    If 'retry_count' < max_retries, increment it and allow re-queue.
    Otherwise mark as skipped.
    """

    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries

    def apply_retry(self, prompt: Prompt) -> bool:
        if prompt.is_failed and prompt.retry_count <= self.max_retries:
            prompt.retry_count += 1
            prompt.shuffle_user_input()
            print(f"[RetryPolicy] Retrying prompt {prompt.uuid} (attempt {prompt.retry_count}/{self.max_retries})")
            return True
        else:
            return False
