from .element_registry import ElementRegistry

# Singleton instance
element_registry = ElementRegistry()
element_registry.auto_discover()
__all__ = [element_registry]
