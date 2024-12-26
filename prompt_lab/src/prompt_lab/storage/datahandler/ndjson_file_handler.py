"""
ndjson_file_handler.py

A DataHandler for Newline-Delimited JSON (NDJSON). This format is inherently
efficient for appending and line-by-line streaming.
"""

import os
import json
from typing import Any, Dict, Iterator, List

from .data_handler import DataHandler


class NDJSONFileHandler(DataHandler):
    """
    Handles a NDJSON file (one JSON object per line).
    """

    def __init__(self, file_path: str):
        """
        :param file_path: Path to the NDJSON file.
        """
        self.file_path = file_path

    def read_data(self) -> Iterator[Dict[str, Any]]:
        """
        Stream records from the NDJSON file line by line.
        """
        if not os.path.exists(self.file_path):
            return iter([])

        with open(self.file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    yield json.loads(line)

    def append_record(self, record: Dict[str, Any]) -> None:
        """
        Append a single record as a new line.
        """
        with open(self.file_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def append_records(self, records: List[Dict[str, Any]]) -> None:
        """
        Append multiple records at once, each on its own line.
        """
        if not records:
            return
        with open(self.file_path, 'a', encoding='utf-8') as f:
            for record in records:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def close(self) -> None:
        """
        No resources to close; NDJSON writes are immediate.
        """
        pass
