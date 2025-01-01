from threading import Lock
from .prompt_tracker import PromptsTracker


class PromptTrackerSingleton:
    """
    Singleton class for managing a single instance of PromptsTracker.
    Allows external initialization with a repository.
    """
    _instance = None
    _lock = Lock()

    @classmethod
    def initialize(cls, repository):
        """
        Initialize the PromptsTracker singleton with a repository.

        :param repository: A repository instance (e.g., HybridHFMongoRepository).
        """
        with cls._lock:
            if cls._instance is None:
                cls._instance = PromptsTracker(repository)
            else:
                raise RuntimeError("TrackerSingleton is already initialized.")

    @classmethod
    def get_instance(cls) -> PromptsTracker:
        """
        Get the singleton instance of PromptsTracker.
        Ensure it is initialized before calling.

        :return: The singleton instance of PromptsTracker.
        """
        if cls._instance is None:
            raise RuntimeError(
                "TrackerSingleton is not initialized. Call `initialize(repository)` first."
            )
        return cls._instance
