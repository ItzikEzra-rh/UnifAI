from typing import Any


class RetrieverCapableMixin:
    """Adds document retrieval."""

    def __init__(self, *, retriever: Any = None, **kwargs: Any):
        super().__init__(**kwargs)  # MRO
        self.retriever = retriever

    def _retrieve(self, query: str) -> str:
        return "" if self.retriever is None else self.retriever.retrieve(query)
