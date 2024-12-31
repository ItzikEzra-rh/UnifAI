from policies.skip.skip_policy import SkipPolicy
from prompt import Prompt


class RetryExceededSkipPolicy(SkipPolicy):
    """
    Example: If prompt.token_count > max_token_limit, skip the prompt and record it in the repository.
    """

    def __init__(self, repository, max_retries: int = 3):
        self.repository = repository
        self.max_retry = max_retries

    def should_skip(self, prompt: Prompt) -> bool:
        if prompt.is_failed and prompt.retry_count > self.max_retry:
            # Mark skip reason
            prompt.set_skip_reason("max retry exceeded")
            # Save to "skipped" data in the repository
            self.repository.save_skipped_data(prompt.to_dict())
            print(f"[SkipPolicy] Skipped prompt due to max retry {prompt.retry_count}/{self.max_retry} exceeded: {prompt.uuid}")
            return True
        return False
