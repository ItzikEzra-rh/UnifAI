class RuntimeContext:
    """
    Singleton-style context holder for active RuntimeState.
    Used by nodes/tools to access logger, metadata, etc.
    """

    _runtime_state = None

    @classmethod
    def set_state(cls, runtime_state):
        cls._runtime_state = runtime_state

    @classmethod
    def get_state(cls):
        if cls._runtime_state is None:
            raise RuntimeError("RuntimeContext not initialized.")
        return cls._runtime_state

    @classmethod
    def get_logger(cls):
        return cls.get_state().get_logger()

    @classmethod
    def clear(cls):
        cls._runtime_state = None
