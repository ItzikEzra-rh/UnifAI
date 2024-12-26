"""
huggingface_data_handler.py

A DataHandler that reads a Hugging Face dataset and buffers appended records
in memory. Appending to a remote dataset typically requires rewriting/pushing
the entire dataset.
"""

from datasets import load_dataset, Dataset, DatasetDict, concatenate_datasets
from typing import Any, Dict, Iterator, List
from .data_handler import DataHandler


class HuggingFaceDataHandler(DataHandler):
    """
    Handles a Hugging Face dataset for reading and buffering appends.
    If streaming=True, reading is done in a memory-efficient manner.
    Appends are merged in memory; pushing to the Hub is a separate action.
    """

    def __init__(
            self,
            repo_id: str,
            split: str = "train",
            streaming: bool = False,
            token: str = None,
            buffer_size: int = 100
    ):
        """
        :param repo_id: The dataset repository ID on Hugging Face, e.g. "user/my_dataset".
        :param split: Which split to load (e.g. "train", "test").
        :param streaming: Whether to load the dataset in streaming mode.
        :param token: Authentication token for private datasets.
        :param buffer_size: Number of records to buffer before merging into the dataset.
        """
        self.repo_id = repo_id
        self.split = split
        self.streaming = streaming
        self.token = token
        self.buffer_size = buffer_size
        self._buffer: List[Dict[str, Any]] = []

        dataset = load_dataset(
            repo_id,
            split=split,
            streaming=streaming,
            use_auth_token=token
        )
        if isinstance(dataset, DatasetDict):
            self._dataset = dataset[self.split]
        else:
            self._dataset = dataset

    def read_data(self) -> Iterator[Dict[str, Any]]:
        """
        Stream records from the Hugging Face dataset. If streaming=True,
        dataset is an IterableDataset and yields items lazily.
        """
        for record in self._dataset:
            yield dict(record)

    def append_record(self, record: Dict[str, Any]) -> None:
        """
        Buffer a record; flush if buffer is full. Actual merging
        happens in memory.
        """
        self._buffer.append(record)
        if len(self._buffer) >= self.buffer_size:
            self._flush_buffer()

    def append_records(self, records: List[Dict[str, Any]]) -> None:
        """
        Append multiple records in one call.
        """
        self._buffer.extend(records)
        if len(self._buffer) >= self.buffer_size:
            self._flush_buffer()

    def _flush_buffer(self) -> None:
        if not self._buffer:
            return

        new_ds = Dataset.from_dict(self._dict_list_to_columns(self._buffer))
        self._dataset = concatenate_datasets([self._dataset, new_ds])
        self._buffer.clear()

    @staticmethod
    def _dict_list_to_columns(records: List[Dict[str, Any]]) -> Dict[str, List[Any]]:
        """
        Convert a list of dicts into a column-oriented dict for building a Hugging Face Dataset.
        """
        if not records:
            return {}
        all_keys = set()
        for r in records:
            all_keys.update(r.keys())

        return {
            k: [r.get(k) for r in records]
            for k in sorted(all_keys)
        }

    def close(self) -> None:
        """
        Flush remaining buffer. If you want to push to hub,
        you'd do so here or after close.
        """
        self._flush_buffer()
        # Optional: self._dataset.push_to_hub(...)
