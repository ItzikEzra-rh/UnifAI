
from abc import ABC, abstractmethod
from models.prompt import Prompt
from typing import List

class BatchStrategy(ABC):
    """
    Defines constraints to decide if a prompt can be added to the batch.
    """

    @abstractmethod
    def can_add_prompt(self, current_batch: List[Prompt], new_prompt: Prompt) -> bool:
        """
        Return True if 'new_prompt' can be added to 'current_batch' without violating constraints.
        """
        pass
