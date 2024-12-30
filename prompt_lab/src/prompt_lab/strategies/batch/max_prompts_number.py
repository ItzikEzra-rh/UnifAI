from typing import List
from prompt import Prompt
from .batch_strategy import BatchStrategy


class MaxPromptsNumber(BatchStrategy):
    """
    Example strategy checking:
      - max number of prompts in a batch
      - max total tokens in the batch
    """

    def __init__(self, max_prompts: int):
        self.max_prompts = max_prompts

    def can_add_prompt(self, current_batch: List[Prompt], new_prompt: Prompt) -> bool:
        # check size limit
        if len(current_batch) >= self.max_prompts:
            return False
        return True
