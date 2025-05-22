class RetrieverCapableMixin:
    """Adds document retrieval."""

    def __init__(self, *, retriever=None, **_):
        self.retriever = retriever

    def _retrieve(self, query: str) -> str:
        return "" if self.retriever is None else self.retriever.retrieve(query)
