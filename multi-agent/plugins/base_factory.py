from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar, Dict

# Type variables for config schema and return type
Cfg = TypeVar("Cfg")
Out = TypeVar("Out")


class BaseFactory(ABC, Generic[Cfg, Out]):
    """
    Abstract interface for all plugin factories (LLMs, tools, nodes, retrievers, etc.).

    Defines a two‐step contract:
      1) accepts(cfg) → bool
           “Do I know how to build from this config?”
      2) create(cfg, **deps) → Out
           “Given a validated config and any injected dependencies,
            produce the plugin instance.”

    This lets PluginRegistry and NodeFactory remain agnostic to specific
    plugin types, while still enabling drop-in extensions via new factories.
    """

    @abstractmethod
    def accepts(self, cfg: Cfg) -> bool:
        """
        Return True if this factory can build an instance from the given config.

        :param cfg: A validated configuration object (Pydantic model).
        :return: True if create(cfg, **deps) will succeed.
        """
        ...

    @abstractmethod
    def create(self, cfg: Cfg, **deps: Any) -> Out:
        """
        Instantiate and return the plugin from the given config.

        :param cfg: A validated configuration object.
        :param deps: Arbitrary keyword‐injected dependencies (e.g. llm, tools, retriever).
        :raises Exception: on invalid config or instantiation failure.
        :return: The created plugin instance.
        """
        ...
