from .prompt_policy import PromptPolicy
from ..prompt import Prompt
from prompt_lab.utils import logger


class PromptReviewFailRetry(PromptPolicy):

    def __init__(self, max_retry=3):
        self.max_retry = max_retry

    def apply(self, prompt: Prompt) -> bool:
        """
        Mark the prompt as failed if:
          1. The prompt review has failed, AND
          2. Either the question or answer generation retry count has exceeded self.max_retry.
        """
        if prompt.review_failed and (
                prompt.question_gen_retry_count > self.max_retry
                or prompt.answer_gen_retry_count > self.max_retry
        ):
            prompt.failed = True
            fail_reason = f"[PromptReviewFailRetry] Prompt {prompt.uuid} failed due to exceeding the "
            f"max retry limit of {self.max_retry}. "
            f"(question_gen_retry_count={prompt.question_gen_retry_count}, "
            f"answer_gen_retry_count={prompt.answer_gen_retry_count})"
            prompt.set_fail_reason(fail_reason)
            logger.info(fail_reason)
            return True

        return False
