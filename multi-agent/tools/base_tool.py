from abc import ABC, abstractmethod

class BaseTool(ABC):
    """
    Standard tool interface.
    """

    @abstractmethod
    def invoke(self, input_data: dict) -> dict:
        """
        Processes the input data and returns a dictionary as output.
        """
        pass

    @abstractmethod
    def name(self) -> str:
        """
        Unique name/identifier of the tool.
        """
        pass
