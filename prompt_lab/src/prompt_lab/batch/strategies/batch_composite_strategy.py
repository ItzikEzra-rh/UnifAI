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
            if not strategy.apply(current_batch, new_prompt):
                return False
        return True

    @property
    def blocker(self) -> bool:
        """Indicates whether the strategy is a blocker."""
        return any(strategy.blocker for strategy in self.strategies)

    def is_blocker(self, current_batch: List[Prompt], new_prompt: Prompt):
        return any(strategy.is_blocker(current_batch, new_prompt) for strategy in self.strategies)
