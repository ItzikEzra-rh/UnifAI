from typing import List
from prompt import Prompt
from .batch_strategy import BatchStrategy


class BatchMaxTokenStrategy(BatchStrategy):
    """
    Example strategy checking:
      - max total tokens in the batch
    """

    def __init__(self, max_total_tokens: int):
        self.max_total_tokens = max_total_tokens

    def apply(self, current_batch: List[Prompt], new_prompt: Prompt) -> bool:
        # check token limit
        current_sum = sum(p.token_count for p in current_batch)
        if current_sum + new_prompt.token_count > self.max_total_tokens:
            return False

        return True

    @property
    def blocker(self) -> bool:
        """Indicates whether the strategy is a blocker."""
        return True
