from typing import List
from prompt import Prompt
from .batch_strategy import BatchStrategy


class BatchRetryPromptsStrategy(BatchStrategy):
    """
    Example strategy checking:
      - max total tokens in the batch
    """

    def apply(self, current_batch: List[Prompt], new_prompt: Prompt) -> bool:
        # check token limit
        is_retry_prompts = all(prompt.is_review_failed and not prompt.failed for prompt in current_batch)
        if is_retry_prompts and new_prompt.is_review_failed and not new_prompt.failed:
            return True

        return False

    @property
    def blocker(self) -> bool:
        """Indicates whether the strategy is a blocker."""
        return False
