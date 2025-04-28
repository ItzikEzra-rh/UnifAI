# plugins/plugin_registry.py

import pkgutil
import importlib
import inspect
from threading import RLock
from typing import Any, Dict, List, Union, Callable

from registry.component_registry import ComponentRegistry
from plugins.base_factory import BaseFactory
from plugins.exceptions import PluginConfigurationError
from registry import registry


class PluginRegistry:
    """
    A hybrid registry that combines:
      - A static ComponentRegistry for pre-registered, shareable components.
      - Dynamic discovery of plugin factories under:
          plugins.llm_factories,
          plugins.tool_factories,
          plugins.agent_factories,
          plugins.retriever_factories.

    Responsibilities:
      * On init, discovers all BaseFactory subclasses in each factory package.
      * Caches created instances per-session.
      * Falls back to ComponentRegistry for string lookups.
      * Provides get_llm, get_tool, get_agent, get_retriever methods.
    """

    def __init__(self):
        self.base = registry
        self._lock = RLock()

        # Discover factories once
        self.llm_factories = self._discover_factories("plugins.llm_factories")
        self.tool_factories = self._discover_factories("plugins.tool_factories")
        self.agent_factories = self._discover_factories("plugins.agent_factories")
        self.ret_factories = self._discover_factories("plugins.retriever_factories")

        # Caches to avoid re-instantiation
        self._llm_cache: Dict[str, Any] = {}
        self._tool_cache: Dict[str, Any] = {}
        self._agent_cache: Dict[str, Any] = {}
        self._ret_cache: Dict[str, Any] = {}

    def _discover_factories(self, pkg_name: str) -> List[BaseFactory]:
        """
        Dynamically import and instantiate all BaseFactory subclasses
        in the given package.

        :param pkg_name: e.g. "plugins.llm_factories"
        :return: List of factory instances.
        """
        factories: List[BaseFactory] = []
        try:
            pkg = importlib.import_module(pkg_name)
        except ModuleNotFoundError:
            return factories

        for _, module_name, _ in pkgutil.iter_modules(pkg.__path__):
            module = importlib.import_module(f"{pkg_name}.{module_name}")
            for attr in vars(module).values():
                if inspect.isclass(attr) and issubclass(attr, BaseFactory) and attr is not BaseFactory:
                    factories.append(attr())
        return factories

    def _resolve(
            self,
            key_or_cfg: Union[str, Dict[str, Any]],
            factories: List[BaseFactory],
            cache: Dict[str, Any],
            static_getter: Callable[[str], Any],
            kind: str
    ) -> Any:
        """
        Core resolution logic: if `key_or_cfg` is a string, do a static lookup;
        if it's a dict, find the first factory that accepts it, create and cache.

        :param key_or_cfg: Name or configuration dict.
        :param factories: List of factories to try on dict config.
        :param cache: Cache mapping names to instances.
        :param static_getter: base_registry.get_* function for string keys.
        :param kind: Description for error messages.
        """
        with self._lock:
            # STATIC lookup by name
            if isinstance(key_or_cfg, str):
                if key_or_cfg in cache:
                    return cache[key_or_cfg]
                return static_getter(key_or_cfg)

            # DYNAMIC creation by config
            for factory in factories:
                if factory.accepts(key_or_cfg):
                    try:
                        instance = factory.create(key_or_cfg)
                        cache[key_or_cfg["name"]] = instance
                        return instance
                    except Exception as e:
                        raise PluginConfigurationError(
                            f"{kind} factory error: {e}", key_or_cfg
                        ) from e

            # No suitable factory found
            raise PluginConfigurationError(
                f"No {kind} factory found for config", key_or_cfg
            )

    def get_llm(self, key_or_cfg: Union[str, Dict[str, Any]]) -> Any:
        """
        Resolve an LLM instance, either from static registry (by name)
        or dynamically from `plugins.llm_factories`.
        """
        return self._resolve(
            key_or_cfg,
            self.llm_factories,
            self._llm_cache,
            self.base.get_llm,
            kind="LLM"
        )

    def get_tool(self, key_or_cfg: Union[str, Dict[str, Any]]) -> Any:
        """
        Resolve a Tool instance, either from static registry (by name)
        or dynamically from `plugins.tool_factories`.
        """
        return self._resolve(
            key_or_cfg,
            self.tool_factories,
            self._tool_cache,
            self.base.get_tool,
            kind="Tool"
        )

    def get_agent(self, key_or_cfg: Union[str, Dict[str, Any]]) -> Any:
        """
        Resolve an Agent, either from static registry (by name) or dynamically.
        Agent factories receive the registry itself for nested resolution.
        """
        if isinstance(key_or_cfg, str):
            with self._lock:
                if key_or_cfg in self._agent_cache:
                    return self._agent_cache[key_or_cfg]
                return self.base.get_agent(key_or_cfg)

        # Dynamic: agents need registry passed in
        for factory in self.agent_factories:
            if factory.accepts(key_or_cfg):
                try:
                    instance = factory.create(key_or_cfg, self)
                    with self._lock:
                        self._agent_cache[key_or_cfg["name"]] = instance
                    return instance
                except Exception as e:
                    raise PluginConfigurationError(
                        f"Agent factory error: {e}", key_or_cfg
                    ) from e

        raise PluginConfigurationError("No Agent factory found for config", key_or_cfg)

    def get_retriever(self, key_or_cfg: Union[str, Dict[str, Any]]) -> Any:
        """
        Resolve a Retriever purely via dynamic factories
        (`plugins.retriever_factories`). Static retrievers are not supported
        by default but could be added to ComponentRegistry if needed.
        """
        # We reuse _resolve but pass a dummy static_getter that always fails
        return self._resolve(
            key_or_cfg,
            self.ret_factories,
            self._ret_cache,
            static_getter=lambda name: (_ for _ in ()).throw(
                KeyError(f"Retriever '{name}' not found")
            ),
            kind="Retriever"
        )
