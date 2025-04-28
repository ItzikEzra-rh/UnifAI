import importlib
import pkgutil
import threading
from typing import Dict, Any, Optional


class ElementRegistry:
    """
    Central catalog of available Nodes, LLMs, Agents, and Tools.
    Built at startup via decorators and auto-discovery.
    Singleton implementation.
    """

    _instance = None
    _lock = threading.Lock()  # To make thread-safe if needed

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(ElementRegistry, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return  # Already initialized once
        self.elements: Dict[str, Dict[str, Any]] = {}
        self._initialized = True

    # --- Registration ---

    def register(self, *, name: str, element_type: str, description: str = "", config_schema: type = None,
                 cls: type = None) -> None:
        if name in self.elements:
            raise ValueError(f"Element '{name}' already registered.")

        self.elements[name] = {
            "type": element_type,
            "description": description,
            "config_schema": config_schema,
            "cls": cls,
        }

    # --- Discovery ---

    def list_elements(self, type_filter: Optional[str] = None) -> list[Dict[str, Any]]:
        """List all registered elements, optionally filtered by type."""
        return [
            {"name": name, **meta}
            for name, meta in self.elements.items()
            if type_filter is None or meta["type"] == type_filter
        ]

    def get_metadata(self, name: str) -> Dict[str, Any]:
        """Get metadata (type, description, schema) for an element."""
        if name not in self.elements:
            raise KeyError(f"Element '{name}' not found.")
        return self.elements[name]

    def get_factory_or_class(self, name: str) -> Any:
        """Get the class or factory responsible for creating this element."""
        if name not in self.elements:
            raise KeyError(f"Element '{name}' not found.")
        return self.elements[name]["cls"]

    def get_schema(self, name: str) -> Optional[type]:
        """Return the associated config schema for an element."""
        if name not in self.elements:
            raise KeyError(f"Element '{name}' not found.")
        return self.elements[name]["config_schema"]

    def has_element(self, name: str) -> bool:
        """Check if an element exists."""
        return name in self.elements

    # --- Auto discovery at startup ---

    def auto_discover(self):
        """
        Imports all modules under `multi_agent.plugins/` and `multi_agent.nodes/`
        to trigger @register_element decorators.
        """
        search_paths = [
            "multi_agent.plugins"
        ]

        for base_package in search_paths:
            try:
                base_dir = base_package.replace(".", "/")
                for finder, name, ispkg in pkgutil.walk_packages([base_dir], prefix=base_package + "."):
                    if not ispkg:
                        importlib.import_module(name)
            except Exception as e:
                print(f"Failed to import from {base_package}: {e}")
