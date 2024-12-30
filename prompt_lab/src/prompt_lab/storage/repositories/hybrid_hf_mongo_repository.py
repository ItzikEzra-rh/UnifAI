# hybrid_hf_mongo_repository.py

"""
hybrid_hf_mongo_repository.py

Uses a HuggingFaceDataHandler for input, MongoDataHandler for processed/skipped/progress,
and defers export logic to an HFExporter.
"""

from typing import Dict, Any, Iterator, Set
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

    # Required interface
    def load_data(self) -> Iterator[Dict[str, Any]]:
        return self.input_handler.read_data()

    def get_input_size(self) -> int:
        return self.input_handler.get_size()

    def input_load_data(self) -> Iterator[Dict[str, Any]]:
        return self.processed_handler.read_data()

    def load_skipped_data(self) -> Iterator[Dict[str, Any]]:
        return self.skipped_handler.read_data()

    def save_processed_data(self, data: Dict[str, Any]) -> None:
        self.processed_handler.append_record(data)

    def save_skipped_data(self, data: Dict[str, Any]) -> None:
        self.skipped_handler.append_record(data)

    def save_progress(self, uuid: str, value: str = "") -> None:
        self.progress_handler.append_record({"uuid": uuid})

    def load_progress(self) -> Set[str]:
        progress_processed_uuid = {uuid_obj["uuid"] for uuid_obj in self.progress_handler.read_data()}
        return progress_processed_uuid

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
