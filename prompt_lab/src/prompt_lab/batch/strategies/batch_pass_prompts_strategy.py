from typing import List
from prompt import Prompt
from .batch_strategy import BatchStrategy


class BatchPassPromptsStrategy(BatchStrategy):

    def apply(self, current_batch: List[Prompt], new_prompt: Prompt) -> bool:
        passed_prompts = all(not prompt.is_review_failed and not prompt.failed for prompt in current_batch)
        if passed_prompts and not new_prompt.is_review_failed and not new_prompt.failed:
            return True

        return False

    @property
    def blocker(self) -> bool:
        """Indicates whether the strategy is a blocker."""
        return False
