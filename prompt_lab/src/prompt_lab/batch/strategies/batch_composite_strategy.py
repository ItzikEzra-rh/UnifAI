from typing import List
from .batch_strategy import BatchStrategy
from prompt import Prompt


class BatchCompositeStrategy(BatchStrategy):
    """
    A composite strategy that applies multiple BatchStrategy instances.
    """

    def __init__(self, strategies: List[BatchStrategy]):
        self.strategies = strategies

    def apply(self, current_batch: List[Prompt], new_prompt: Prompt) -> bool:
        """
        Return True only if all strategies agree that the new_prompt can be added.
        """
        for strategy in self.strategies:
            if not strategy.can_add_prompt(current_batch, new_prompt):
                return False
        return True
