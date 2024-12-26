"""
json_file_handler.py

Implements JSONFileHandler, which uses a top-level JSON array on disk.
Supports:
- Streaming reads with ijson
- Single or multiple appends using minimal overhead end-of-file manipulation
"""

import os
import ijson
import json
from typing import Any, Dict, Iterator, List

from .data_handler import DataHandler
from utils.util import (
    append_to_json_list,
    append_multiple_to_json_list
)


class JSONFileHandler(DataHandler):
    """
    A DataHandler for a JSON file containing a single top-level array.
    Provides:
      - Streaming read via ijson
      - Single-record or multi-record appends via end-of-file manipulation
    """

    def __init__(self, file_path: str):
        """
        :param file_path: Path to the JSON file (containing a top-level array).
        """
        self.file_path = file_path

    def read_data(self) -> Iterator[Dict[str, Any]]:
        """
        Stream items from the file's JSON array using ijson. This avoids
        loading the entire file at once.

        :return: An iterator of dict records.
        """
        if not os.path.exists(self.file_path):
            return iter([])

        with open(self.file_path, 'rb') as f:
            try:
                # ijson.items: "item" references each element of the top-level list
                for record in ijson.items(f, "item"):
                    yield record
            except ijson.common.IncompleteJSONError:
                raise ValueError("JSON file is incomplete or invalid.")
            except ijson.JSONError as e:
                raise ValueError(f"Error parsing JSON file: {e}")

    def append_record(self, record: Dict[str, Any]) -> None:
        """
        Append a single record to the JSON array on disk.
        """
        append_to_json_list(self.file_path, record)

    def append_records(self, records: List[Dict[str, Any]]) -> None:
        """
        Append multiple records in one call, which is more efficient
        than appending them one by one.
        """
        append_multiple_to_json_list(self.file_path, records)

    def close(self) -> None:
        """
        No resources to close; each append is done immediately.
        """
        pass

    def append_to_object(self, key: str, val: Any) -> None:
        """
        If you want to treat the top-level JSON as an object, you'd have to do a
        read-modify-write approach. This isn't recommended if you store data as a list.
        """

        # Basic fallback: load entire file, confirm it's an object, set key, rewrite.
        if not os.path.exists(self.file_path):
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump({key: val}, f)
            return

        with open(self.file_path, 'r+', encoding='utf-8') as f:
            try:
                data = json.load(f)
                if not isinstance(data, dict):
                    data = {}
            except json.JSONDecodeError:
                data = {}

            data[key] = val
            f.seek(0)
            json.dump(data, f, indent=2)
            f.truncate()
