from typing import Dict, Any


class PromptsTracker:
    """
    Generic tracker for prompts progress, independent of the underlying storage.
    """

    DEFAULT_PROGRESS_ID = "progress_data"
    DEFAULT_VALUES = {
        "number_of_elements": 0,
        "prompts_generated": 0,
        "prompts_retried": 0,
        "prompts_failed": 0,
        "prompts_skipped": 0,
        "prompts_pass": 0,
        "prompts_processed": 0,
    }

    def __init__(self, repository):
        """
        :param repository: A repository with high-level methods for managing progress data.
        """
        self.repository = repository
        self._initialize_progress_data()

    def _initialize_progress_data(self) -> None:
        """
        Ensure progress data exists in the repository, initializing it if necessary.
        """
        existing_data = self.repository.get_progress_data(self.DEFAULT_PROGRESS_ID)
        if not existing_data:
            self.repository.save_progress_data(
                self.DEFAULT_PROGRESS_ID, self.DEFAULT_VALUES
            )

    def increment(self, key: str, amount: int = 1) -> None:
        """
        Increment a specific progress key.

        :param key: The key to increment.
        :param amount: The amount to increment by.
        """
        if key not in self.DEFAULT_VALUES:
            raise ValueError(f"Invalid progress key: {key}")

        self.repository.increment_progress(self.DEFAULT_PROGRESS_ID, key, amount)

    def set_value(self, key: str, value: int) -> None:
        """
        Set a specific progress key to a specific value (e.g., `number_of_elements`).

        :param key: The key to set.
        :param value: The value to set the key to.
        """
        if key not in self.DEFAULT_VALUES:
            raise ValueError(f"Invalid progress key: {key}")

        self.repository.save_progress_data(
            self.DEFAULT_PROGRESS_ID, {**self.DEFAULT_VALUES, key: value}
        )

    def get_progress_data(self) -> Dict[str, Any]:
        """
        Retrieve the current progress data.

        :return: A dictionary of progress data.
        """
        return self.repository.get_progress_data(self.DEFAULT_PROGRESS_ID)

    def reset_progress(self) -> None:
        """
        Reset all progress values to their default state.
        """
        self.repository.save_progress_data(
            self.DEFAULT_PROGRESS_ID, self.DEFAULT_VALUES
        )

    # Increment methods with automatic prompts_processed increment
    def _increment_with_processed(self, key: str, amount: int = 1) -> None:
        """
        Increment a specific key and also increment prompts_processed.

        :param key: The key to increment.
        :param amount: The amount to increment by.
        """
        self.increment(key, amount)
        self.increment("prompts_processed", amount)

    def increment_prompts_failed(self, amount: int = 1) -> None:
        self._increment_with_processed("prompts_failed", amount)

    def increment_prompts_skipped(self, amount: int = 1) -> None:
        self._increment_with_processed("prompts_skipped", amount)

    def increment_prompts_pass(self, amount: int = 1) -> None:
        self._increment_with_processed("prompts_pass", amount)

    # Other increment methods
    def increment_prompts_generated(self, amount: int = 1) -> None:
        self.increment("prompts_generated", amount)

    def increment_prompts_retried(self, amount: int = 1) -> None:
        self.increment("prompts_retried", amount)

    def set_number_of_elements(self, value: int) -> None:
        self.set_value("number_of_elements", value)
