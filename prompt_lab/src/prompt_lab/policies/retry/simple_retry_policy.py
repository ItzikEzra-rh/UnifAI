from .retry_policy import RetryPolicy


class SimpleRetryPolicy(RetryPolicy):
    """
    If 'retry_count' < max_retries, increment it and allow re-queue.
    Otherwise mark as skipped.
    """

    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries

    def apply_retry_logic(self, prompt: Prompt) -> bool:
        current_retry = prompt.metadata.get("retry_count", 0)
        if current_retry < self.max_retries:
            prompt.metadata["retry_count"] = current_retry + 1
            # Clear any skip reason if it exists
            if "skip" in prompt.metadata:
                del prompt.metadata["skip"]
            print(f"[RetryPolicy] Retrying prompt {prompt.uuid} (attempt {current_retry + 1})")
            return True
        else:
            prompt.metadata.setdefault("skip", {})
            prompt.metadata["skip"]["reason"] = "exceeded_max_retries"
            print(f"[RetryPolicy] Prompt {prompt.uuid} exceeded max retries -> skip")
            return False
