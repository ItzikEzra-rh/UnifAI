from abc import ABC, abstractmethod
from prompt_lab.prompt import Prompt
from typing import List


class BatchStrategy(ABC):
    """
    Defines constraints to decide if a prompt can be added to the batch.
    """

    @abstractmethod
    def apply(self, current_batch: List[Prompt], new_prompt: Prompt) -> bool:
        """
        Return True if 'new_prompt' can be added to 'current_batch' without violating constraints.
        """
        pass

    @property
    @abstractmethod
    def blocker(self) -> bool:
        """Indicates whether the strategy is a blocker."""
        pass

    def is_blocker(self, current_batch: List[Prompt], new_prompt: Prompt):
        return not self.apply(current_batch, new_prompt) and self.blocker
