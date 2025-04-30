from abc import ABC, abstractmethod


class BaseLLM(ABC):
    """
    Abstract base class for all LLM integrations (OpenAI, LlamaStack, etc.)
    """

    @abstractmethod
    def chat(self, messages: list[dict], stream: bool = False) -> str:
        """
        Perform a conversational completion.
        messages = list of {"role": "user"/"assistant", "content": "..."}
        """
        pass

    @abstractmethod
    def name(self) -> str:
        """
        Returns the identifier for the LLM (for logging/debug).
        """
        pass
