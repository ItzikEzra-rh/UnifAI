# hybrid_hf_mongo_repository.py

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
            processed_handler: MongoDataHandler,
            skipped_handler: MongoDataHandler,
            progress_handler: MongoDataHandler,
            exporter: HFExporter = None
    ):
        """
        :param input_handler: HuggingFaceDataHandler for input.
        :param processed_handler: MongoDataHandler for processed docs.
        :param skipped_handler: MongoDataHandler for skipped docs.
        :param progress_handler: MongoDataHandler for progress docs.
        :param exporter: Optionally inject an HFExporter instance.
        """
        self.input_handler = input_handler
        self.processed_handler = processed_handler
        self.skipped_handler = skipped_handler
        self.progress_handler = progress_handler
        self.exporter = exporter or HFExporter()

    # input handler
    def load_input_data(self) -> Iterator[Dict[str, Any]]:
        return self.input_handler.read_data()

    def get_input_size(self) -> int:
        return self.input_handler.get_size()

    # processed_handler
    def save_processed_data(self, data: List[Dict[str, Any]]) -> None:
        """
        Save processed data to the MongoDB collection. Ensures that the `uuid` field
        is used as the `_id` for uniqueness.

        :param data: A list of dictionaries representing the records to save.
        """
        if not data:
            return

        # Transform records to use `uuid` as `_id`
        transformed_data = [{**record, "_id": record["uuid"]} for record in data]

        try:
            self.processed_handler.append_records(transformed_data)
        except Exception as e:
            # Handle duplicate key error or log as needed
            print(f"Error while inserting records: {e}")

    def load_processed_data_uuids(self) -> Set[str]:
        """
        Load and return a set of processed UUIDs from the progress handler.

        :return: A set of UUID strings that have been processed.
        """
        # Use projection to fetch only the uuid field
        progress_processed_uuid = {
            uuid_obj["uuid"] for uuid_obj in self.progress_handler.read_data(projection={"uuid": 1, "_id": 0})
        }
        return progress_processed_uuid

    def load_processed_data(self) -> List[Dict[str, Any]]:
        return [data for data in self.progress_handler.read_data()]

    # skip handler
    def load_skipped_data(self) -> Iterator[Dict[str, Any]]:
        return self.skipped_handler.read_data()

    def save_skipped_data(self, data: Dict[str, Any]) -> None:
        self.skipped_handler.append_record(data)

    # progress handler
    def get_progress_data(self, progress_id: str) -> Dict[str, Any]:
        """
        Retrieve progress data by ID.
        """
        cursor = self.progress_handler.read_data(query={"_id": progress_id})
        return next(cursor, {})

    def save_progress_data(self, progress_id: str, data: Dict[str, Any]) -> None:
        """
        Save or overwrite progress data by ID.
        """
        self.progress_handler.update_record(
            query={"_id": progress_id}, update={"$set": data}, upsert=True
        )

    def increment_progress(self, progress_id: str, key: str, amount: int) -> None:
        """
        Increment a specific progress key for a given progress ID.
        """
        self.progress_handler.update_record(
            query={"_id": progress_id}, update={"$inc": {key: amount}}
        )

    def close(self) -> None:
        self.input_handler.close()
        self.processed_handler.close()
        self.skipped_handler.close()
        self.progress_handler.close()
        # The exporter doesn’t hold open resources by default, so no need to close it.

    # Additional method for exporting
    def export_processed_data_to_huggingface(
            self,
            repo_id: str,
            local_parquet_path: str = "processed.parquet",
            hf_token: str = None
    ) -> None:
        """
        Gathers processed records from Mongo and delegates the export to HFExporter.
        """
        all_records = list(self.load_processed_data())
        self.exporter.export_records_to_hf(
            records=all_records,
            repo_id=repo_id,
            local_parquet_path=local_parquet_path,
            token=hf_token
        )
