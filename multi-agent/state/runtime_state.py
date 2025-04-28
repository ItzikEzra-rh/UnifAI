class RuntimeState:
    """
    Holds the current state of graph execution, including:
    - compiled graph
    - graph plan
    - logger
    - runtime metadata
    """

    def __init__(self, plan, graph, logger=None, metadata=None):
        self.plan = plan          # GraphPlan instance
        self.graph = graph        # Compiled graph (LangGraph, etc.)
        self.logger = logger      # LoggerInterface-compatible
        self.metadata = metadata or {}  # e.g., version, run_id, source

    def attach_logger(self, logger):
        self.logger = logger

    def get_logger(self):
        return self.logger

    def update_metadata(self, key, value):
        self.metadata[key] = value
