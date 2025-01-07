from abc import ABC, abstractmethod
from ..prompt import Prompt


class PromptPolicy(ABC):
    """
    Decides if/how a prompt can be retried.
    """

    @abstractmethod
    def apply(self, prompt: Prompt) -> bool:
        """
        Return True if we are applied policy on Prompt, else return False.
        """
        pass
