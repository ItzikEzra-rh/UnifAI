from .prompt_policy import PromptPolicy
from ..prompt import Prompt
from prompt_lab.utils import logger


class PromptReviewFailRetry(PromptPolicy):

    def __init__(self, max_retry=3):
        self.max_retry = max_retry

    def apply(self, prompt: Prompt) -> bool:
        if prompt.review_failed and prompt.retry_count > self.max_retry:
            prompt.failed = True
            prompt.set_fail_reason(self.__class__.__name__)
            logger.info(
                f"[PromptReviewFailRetry] Failed prompt due to retry count {prompt.retry_count} and it exceeded max "
                f"retry {self.max_retry} : {prompt.uuid}")
            return True
        return False
