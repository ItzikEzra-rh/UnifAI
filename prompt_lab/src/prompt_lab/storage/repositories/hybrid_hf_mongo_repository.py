"""
hybrid_hf_mongo_repository.py

Uses a HuggingFaceDataHandler for input, MongoDataHandler for processed/skipped/progress,
and defers export logic to an HFExporter.
"""

from typing import Dict, Any, Iterator, Set, List
from storage import (DataRepository,
                     HuggingFaceDataHandler,
                     MongoDataHandler,
                     HFExporter)
from storage.stats.stats import Stats


class HybridHFMongoRepository(DataRepository):
    """
    Hybrid repository:
      - input: HuggingFaceDataHandler
      - processed/skipped/progress: MongoDataHandler
      - delegates export to HFExporter
    """

    def __init__(
            self,
            input_handler: HuggingFaceDataHandler,
            pass_handler: MongoDataHandler,
            fail_handler: MongoDataHandler,
            stats_handler: MongoDataHandler,
            exporter: HFExporter
    ):
        self.input_handler = input_handler
        self.pass_handler = pass_handler
        self.fail_handler = fail_handler
        self.stats_handler = Stats(stats_handler)
        self.exporter = exporter

    # input handler
    def load_input_data(self) -> Iterator[Dict[str, Any]]:
        return self.input_handler.read_data()

    def get_input_size(self) -> int:
        size = self.input_handler.get_size()
        self.stats_handler.set_number_of_elements(size)
        return size

    # processed_handler
    def save_pass_prompts(self, prompts: List[Dict]) -> None:
        """
        Save processed data to the MongoDB collection. Ensures that the `uuid` field
        is used as the `_id` for uniqueness.

        :param data: A list of dictionaries representing the records to save.
        """
        # Transform records to use `uuid` as `_id`
        transformed_data = [{**record, "_id": record["uuid"]} for record in prompts]

        try:
            self.pass_handler.append_records(transformed_data)
            self.stats_handler.increment_prompts_pass(amount=len(prompts))
        except Exception as e:
            # Handle duplicate key error or log as needed
            print(f"Error while inserting records: {e}")

    def load_pass_prompts_uuids(self) -> Set[str]:
        """
        Load and return a set of processed UUIDs from the progress handler.

        :return: A set of UUID strings that have been processed.
        """
        # Use projection to fetch only the uuid field
        pass_processed_uuid = {
            uuid_obj["uuid"] for uuid_obj in self.pass_handler.read_data(projection={"uuid": 1, "_id": 0})
        }
        return pass_processed_uuid

    # fail handler
    def save_fail_prompts(self, prompts: List[Dict]) -> None:
        transformed_data = [{**record, "_id": record["uuid"]} for record in prompts]
        try:
            self.fail_handler.append_records(transformed_data)
            self.stats_handler.increment_prompts_failed(amount=len(prompts))
        except Exception as e:
            # Handle duplicate key error or log as needed
            print(f"Error while inserting records: {e}")

    def load_fail_prompts_uuids(self) -> Set[str]:
        """
        Load and return a set of processed UUIDs from the progress handler.

        :return: A set of UUID strings that have been processed.
        """
        # Use projection to fetch only the uuid field
        fail_processed_uuid = {
            uuid_obj["uuid"] for uuid_obj in self.fail_handler.read_data(projection={"uuid": 1, "_id": 0})
        }
        return fail_processed_uuid

    # stats handler
    def update_retry_counter(self, count: int):
        self.stats_handler.increment_prompts_retried(count)

    def update_prompt_generation_counter(self, count: int = 1):
        self.stats_handler.increment_prompts_generated(count)

    # output
    def export(self):
        if self.stats_handler.is_done():
            self.exporter.export(self.pass_handler.read_data())

    def load_processed_prompts_uuids(self) -> Set[str]:
        return self.load_fail_prompts_uuids().union(self.load_pass_prompts_uuids())

    def close(self) -> None:
        self.input_handler.close()
        self.pass_handler.close()
        self.fail_handler.close()
        self.stats_handler.close()
