"""Template instantiation package."""

from templates.instantiation.instantiator import (
    TemplateInstantiator,
    InstantiationResult,
    MergeError,
)
from templates.instantiation.materializer import (
    ResourceMaterializer,
    MaterializationResult,
    MaterializationError,
)

__all__ = [
    "TemplateInstantiator",
    "InstantiationResult",
    "MergeError",
    "ResourceMaterializer",
    "MaterializationResult",
    "MaterializationError",
]
