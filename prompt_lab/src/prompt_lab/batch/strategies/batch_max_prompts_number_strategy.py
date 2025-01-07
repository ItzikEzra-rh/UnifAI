from typing import List
from prompt_lab.prompt import Prompt
from .batch_strategy import BatchStrategy


class BatchMaxPromptsNumberStrategy(BatchStrategy):
    """
    Example strategy checking:
      - max number of prompts in a batch
      - max total tokens in the batch
    """

    def __init__(self, max_prompts: int):
        self.max_prompts = max_prompts

    def apply(self, current_batch: List[Prompt], new_prompt: Prompt) -> bool:
        # check size limit
        if len(current_batch) >= self.max_prompts:
            return False
        return True

    @property
    def blocker(self) -> bool:
        """Indicates whether the strategy is a blocker."""
        return True
