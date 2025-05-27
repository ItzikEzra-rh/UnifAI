import importlib
import threading
from typing import Dict, List
import os
from registry.element_definition import ElementDefinition


class ElementRegistry:
    """
    Singleton registry of all plugin element definitions, organized
    by category (e.g. "llm", "tool", "retriever", "node") and type_key
    (e.g. "openai", "mock", "slack_agent").

    Each ElementDefinition holds:
      - category: str
      - type_key: str
      - description: str
      - schema_cls: Optional[PydanticModel]
      - factory_cls: BaseFactory subclass
    """

    _instance: "ElementRegistry" = None
    _lock = threading.RLock()

    def __new__(cls) -> "ElementRegistry":
        # Thread-safe lazy singleton instantiation
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    # mark as uninitialized so __init__ runs once
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        # Only initialize once
        if getattr(self, "_initialized", False):
            return
        # _defs maps category -> (type_key -> ElementDefinition)
        self._defs: Dict[str, Dict[str, ElementDefinition]] = {}
        self._initialized = True

    def register_element(self, edef: ElementDefinition) -> None:
        """
        Register a new ElementDefinition under its category/type_key.

        :param edef: The ElementDefinition to register.
        :raises ValueError: if that category/type_key is already registered.
        """
        with self._lock:
            cat_map = self._defs.setdefault(edef.category, {})
            if edef.type_key in cat_map:
                raise ValueError(f"Element already registered: {edef.category}/{edef.type_key}")
            cat_map[edef.type_key] = edef

    def list_types(self, category: str) -> List[str]:
        """
        List all registered type_keys for a given category.

        :param category: e.g. "llm", "tool", "node"
        :return: list of type_key strings
        """
        return list(self._defs.get(category, {}).keys())

    def get_definition(self, category: str, type_key: str) -> ElementDefinition:
        """
        Retrieve the ElementDefinition for a given category and type_key.

        :param category: component category
        :param type_key: specific plugin type
        :raises KeyError: if not found
        """
        try:
            return self._defs[category][type_key]
        except KeyError:
            raise KeyError(f"No element registered under {category}/{type_key}")

    def get_factory(self, category: str, type_key: str):
        """
        Get the factory class for the specified element.

        :param category: component category
        :param type_key: plugin type
        :return: BaseFactory subclass
        """
        return self.get_definition(category, type_key).factory_cls

    def get_schema(self, category: str, type_key: str):
        """
        Get the Pydantic schema class for the specified element.

        :param category: component category
        :param type_key: plugin type
        :return: BaseModel subclass or None
        """
        return self.get_definition(category, type_key).schema_cls

    def get_description(self, category: str, type_key: str) -> str:
        """
        Get the human-readable description for the specified element.

        :param category: component category
        :param type_key: plugin type
        :return: description string
        """
        return self.get_definition(category, type_key).description

    def auto_discover(self):
        """
        Only import Python modules from folders inside `plugins/` that match '*_factories'.
        """
        plugins_dir = os.path.join(os.getcwd(), "plugins")

        if not os.path.isdir(plugins_dir):
            print(f"Plugins directory not found at {plugins_dir}")
            return

        for folder_name in os.listdir(plugins_dir):
            folder_path = os.path.join(plugins_dir, folder_name)

            # Only process directories matching *_factories
            if os.path.isdir(folder_path) and folder_name.endswith("_factories"):
                for filename in os.listdir(folder_path):
                    if filename.endswith(".py") and not filename.startswith("__"):
                        module_name = f"plugins.{folder_name}.{filename[:-3]}"  # Remove '.py'
                        # try:
                        importlib.import_module(module_name)
                            # print(f"Imported {module_name}")
                        # except Exception as e:
                        #     print(f"Failed to import {module_name}: {e}")
