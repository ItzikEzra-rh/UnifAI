from .prompt_policy import PromptPolicy
from prompt import Prompt
from utils import logger


class PromptReviewFailRetry(PromptPolicy):

    def __init__(self, max_retry=3):
        self.max_retry = max_retry

    def apply(self, prompt: Prompt) -> bool:
        if prompt.review_failed and prompt.retry_count > self.max_retry:
            prompt.failed = True
            prompt.set_fail_reason("PromptFailRetry")
            logger.info(
                f"[PromptReviewFailRetry] Failed prompt due to max retry {prompt.retry_count}/{self.max_retry} exceeded: {prompt.uuid}")
            return True
        return False
