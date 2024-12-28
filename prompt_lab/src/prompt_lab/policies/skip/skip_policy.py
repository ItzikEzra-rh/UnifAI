from abc import ABC, abstractmethod
from models.prompt import Prompt

class SkipPolicy(ABC):
    """
    Decides if a prompt should be skipped entirely before adding it to a batch.
    """

    @abstractmethod
    def should_skip(self, prompt: Prompt) -> bool:
        """
        Return True if 'prompt' must be skipped, False if it can proceed.
        """
        pass