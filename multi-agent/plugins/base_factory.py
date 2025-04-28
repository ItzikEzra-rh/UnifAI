from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseFactory(ABC):
    """
    Abstract interface for all dynamic plugin factories.

    Each factory must answer two questions:
      1) `accepts(cfg)` – can this factory build from the given config?
      2) `create(cfg)`  – create and return the plugin instance.

    By coding to this interface, PluginRegistry can remain agnostic
    to specific plugin types and support new ones via drop-in factories.
    """

    @abstractmethod
    def accepts(self, cfg: Dict[str, Any]) -> bool:
        """
        Return True if this factory knows how to handle `cfg`.

        :param cfg: A validated configuration dictionary.
        :return: True if `create(cfg)` will succeed for this factory.
        """
        pass

    @abstractmethod
    def create(self, cfg: Dict[str, Any]) -> Any:
        """
        Instantiate the plugin from `cfg`.

        :param cfg: A validated configuration dictionary.
        :raises Exception: on invalid config or instantiation failure.
        :return: The created plugin instance.
        """
        pass
