"""

Makes it easy to import key classes from storage's submodules
(datahandler, exporters, repository) directly from the `storage` package.
"""

from .batch_composite_strategy import BatchCompositeStrategy

__all__ = [
    "BatchCompositeStrategy"
]
