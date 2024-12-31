from abc import ABC, abstractmethod
from prompt import Prompt


class RetryPolicy(ABC):
    """
    Decides if/how a prompt can be retried.
    """

    @abstractmethod
    def apply_retry(self, prompt: Prompt) -> bool:
        """
        Return True if we are retrying the prompt, False if we skip permanently.
        """
        pass
