import importlib
import threading
from typing import Dict, List, Type
from global_utils.utils.singleton import SingletonMeta
import os
from catalog.element_definition import ElementDefinition
from core.enums import ResourceCategory


class ElementRegistry(metaclass=SingletonMeta):
    """
    Keeps the *in-memory* map   (category → type_key → ElementDefinition).

    ▶  No validation rules
    ▶  No JSON serialisation
    ▶  No DB or HTTP – just look-ups
    """
    _lock = threading.RLock()

    def __init__(self) -> None:
        # (re-)entrancy guard for SingletonMeta
        if getattr(self, "_initialised", False):
            return

        self._defs: Dict[ResourceCategory,
                         Dict[str, ElementDefinition]] = {}

        # Auto-discover once on construction
        self._auto_discover_plugins()

    # ------------------------------------------------------------------ #
    #  Registration / Introspection
    # ------------------------------------------------------------------ #
    def register_element(self, edef: ElementDefinition) -> None:
        with self._lock:
            cat_map = self._defs.setdefault(edef.category, {})
            if edef.type_key in cat_map:
                raise ValueError(f"Duplicate element: {edef.category}/{edef.type_key}")
            cat_map[edef.type_key] = edef

    def list_categories(self) -> List[ResourceCategory]:
        return list(self._defs.keys())

    def list_types(self, category: ResourceCategory) -> List[str]:
        return list(self._defs.get(category, {}).keys())

    def get(self,
            category: ResourceCategory,
            type_key: str) -> ElementDefinition:
        try:
            return self._defs[category][type_key]
        except KeyError:
            raise KeyError(f"No element {category}/{type_key}")

    # ---- short-hand helpers ------------------------------------------
    def get_schema(self, category: ResourceCategory, type_key: str) -> Type:
        return self.get(category, type_key).schema_cls

    def get_factory(self, category: ResourceCategory, type_key: str) -> Type:
        return self.get(category, type_key).factory_cls

    # ------------------------------------------------------------------ #
    #  Utility used by Blueprint-resolver (tell which discriminator = which cat)
    # ------------------------------------------------------------------ #
    def get_category_from_dict(self, raw: dict) -> ResourceCategory:
        """
        Examine typical config dicts that always contain a 'type'
        discriminator and decide which catalogue it belongs to.
        """
        type_key = raw.get("type")
        for cat, mapping in self._defs.items():
            if type_key in mapping:
                return cat
        raise ValueError(f"Cannot infer category for type='{type_key}'")

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
