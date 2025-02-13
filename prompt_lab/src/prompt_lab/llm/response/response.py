from abc import ABC, abstractmethod
from collections import defaultdict


class ResponseProcessor(ABC):
    """
    Abstract base class for processing LLM responses.
    """

    def __init__(self):
        self.responses = defaultdict(str)

    @abstractmethod
    def process_response(self, response):
        """
        Processes an LLM response.

        Args:
            response: The raw response from the LLM.
        """
        pass
