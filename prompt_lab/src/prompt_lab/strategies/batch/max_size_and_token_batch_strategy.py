from typing import List
from models.prompt import Prompt
from strategies.batch_strategy import BatchStrategy

class MaxSizeAndTokenBatchStrategy(BatchStrategy):
    """
    Example strategy checking:
      - max number of prompts in a batch
      - max total tokens in the batch
    """

    def __init__(self, max_prompts: int, max_total_tokens: int):
        self.max_prompts = max_prompts
        self.max_total_tokens = max_total_tokens

    def can_add_prompt(self, current_batch: List[Prompt], new_prompt: Prompt) -> bool:
        # 1) check size limit
        if len(current_batch) >= self.max_prompts:
            return False

        # 2) check token limit
        current_sum = sum(p.token_count for p in current_batch)
        if current_sum + new_prompt.token_count > self.max_total_tokens:
            return False

        return True
