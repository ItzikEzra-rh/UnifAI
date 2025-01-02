from typing import Dict, Any


class Stats:
    """
    Generic tracker for prompts progress, independent of the underlying storage.
    """

    DEFAULT_PROGRESS_ID = "progress_data"
    DEFAULT_VALUES = {
        "number_of_elements": 0,
        "prompts_generated": 0,
        "prompts_retried": 0,
        "prompts_failed": 0,
        "prompts_pass": 0,
        "prompts_processed": 0,
    }

    def __init__(self, statistics_handler):
        """
        :param statistics_handler: A MongoDataHandler instance for managing progress data.
        """
        self.statistics_handler = statistics_handler
        self._progress_data = self.DEFAULT_VALUES.copy()
        self._initialize_progress_data()

    def _initialize_progress_data(self) -> None:
        """
        Ensure progress data exists in the storage, initializing it if necessary.
        """
        existing_data = list(self.statistics_handler.read_data(
            query={"_id": self.DEFAULT_PROGRESS_ID}
        ))
        if not existing_data:
            # Initialize in MongoDB
            self.statistics_handler.append_record({"_id": self.DEFAULT_PROGRESS_ID, **self._progress_data})
        else:
            # Load data from MongoDB into in-memory attributes
            self._progress_data.update(existing_data[0])

    def _sync_to_mongo(self, keys: list = None) -> None:
        """
        Synchronize specific keys or the entire in-memory state to MongoDB.

        :param keys: List of keys to sync. If None, sync all keys.
        """
        if keys is None:
            update_data = self._progress_data
        else:
            update_data = {key: self._progress_data[key] for key in keys if key in self._progress_data}
        self.statistics_handler.update_record(
            query={"_id": self.DEFAULT_PROGRESS_ID}, update={"$set": update_data}
        )

    def _validate_key(self, key: str) -> None:
        """
        Validate if a key is part of the default values.

        :param key: The key to validate.
        :raises ValueError: If the key is invalid.
        """
        if key not in self.DEFAULT_VALUES:
            raise ValueError(f"Invalid progress key: {key}")

    def increment(self, key: str, amount: int = 1) -> None:
        """
        Increment a specific progress key.

        :param key: The key to increment.
        :param amount: The amount to increment by.
        """
        self._validate_key(key)
        self._progress_data[key] += amount
        self._sync_to_mongo(keys=[key])

    def set_value(self, key: str, value: int) -> None:
        """
        Set a specific progress key to a specific value.

        :param key: The key to set.
        :param value: The value to set the key to.
        """
        self._validate_key(key)
        self._progress_data[key] = value
        self._sync_to_mongo(keys=[key])

    def get_stats(self) -> Dict[str, Any]:
        """
        Retrieve the current progress data.

        :return: A dictionary of progress data.
        """
        return self._progress_data.copy()

    def reset_progress(self) -> None:
        """
        Reset all progress values to their default state.
        """
        self._progress_data = self.DEFAULT_VALUES.copy()
        self._sync_to_mongo()

    def increment_with_processed(self, key: str, amount: int = 1) -> None:
        """
        Increment a specific key and also increment `prompts_processed`.

        :param key: The key to increment.
        :param amount: The amount to increment by.
        """
        self.increment(key, amount)
        self.increment("prompts_processed", amount)

    # Convenience increment methods
    def increment_prompts_failed(self, amount: int = 1) -> None:
        self.increment_with_processed("prompts_failed", amount)

    def increment_prompts_pass(self, amount: int = 1) -> None:
        self.increment_with_processed("prompts_pass", amount)

    def increment_prompts_generated(self, amount: int = 1) -> None:
        self.increment("prompts_generated", amount)

    def increment_prompts_retried(self, amount: int = 1) -> None:
        self.increment("prompts_retried", amount)

    def set_number_of_elements(self, value: int) -> None:
        self.set_value("number_of_elements", value)

    def is_done(self) -> bool:
        """
        Check if all generated prompts have been processed.

        :return: True if done, False otherwise.
        """
        return self._progress_data["prompts_generated"] == self._progress_data["prompts_processed"]

    def close(self):
        """
        Close the MongoDataHandler.
        """
        self.statistics_handler.close()
