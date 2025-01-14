"""
parquet_file_handler.py

A Parquet-based DataHandler that buffers appends and writes using a
ParquetWriter for efficiency. Reading is done in streaming batches.
"""

import os
from typing import Any, Dict, Iterator, List, Optional
import pyarrow as pa
import pyarrow.parquet as pq
from .data_handler import DataHandler


class ParquetFileHandler(DataHandler):
    """
    Handles a Parquet file for efficient columnar storage, buffering appended
    records to minimize I/O overhead.
    """

    def __init__(self, file_path: str, buffer_size: int = 100):
        """
        :param file_path: Path to the Parquet file.
        :param buffer_size: Number of records to buffer before writing to disk.
        """
        self.file_path = file_path
        self.buffer_size = buffer_size
        self._buffer: List[Dict[str, Any]] = []
        self._writer: Optional[pq.ParquetWriter] = None
        self._schema: Optional[pa.Schema] = None

        # If file exists, read schema so we can append consistently.
        if os.path.exists(self.file_path):
            try:
                table = pq.read_table(self.file_path)
                self._schema = table.schema
            except Exception:
                # If not a valid parquet or corrupted, we ignore.
                pass

    def read_data(self) -> Iterator[Dict[str, Any]]:
        """
        Stream data from the Parquet file in batches.
        """
        if not os.path.exists(self.file_path):
            return iter([])

        parquet_file = pq.ParquetFile(self.file_path)
        for batch in parquet_file.iter_batches():
            table = pa.Table.from_batches([batch])
            table_dict = table.to_pydict()
            num_rows = len(table_dict[next(iter(table_dict), "")]) if table_dict else 0
            for i in range(num_rows):
                yield {col: table_dict[col][i] for col in table_dict}

    def append_record(self, record: Dict[str, Any]) -> None:
        """
        Buffer a single record and flush when buffer is full.
        """
        self._buffer.append(record)
        if len(self._buffer) >= self.buffer_size:
            self._flush_buffer()

    def append_records(self, records: List[Dict[str, Any]]) -> None:
        """
        Append multiple records efficiently in one go, potentially
        reducing flush frequency.
        """
        self._buffer.extend(records)
        if len(self._buffer) >= self.buffer_size:
            self._flush_buffer()

    def _initialize_writer(self, table: pa.Table) -> None:
        """
        Initialize a ParquetWriter if not already open.
        """
        if self._writer is not None:
            return

        if self._schema is None:
            self._schema = table.schema

        self._writer = pq.ParquetWriter(
            self.file_path,
            self._schema,
            use_dictionary=True,
            compression="snappy",
        )

    def _flush_buffer(self) -> None:
        """
        Convert buffer to a Table and write it using the ParquetWriter.
        """
        if not self._buffer:
            return

        # Build columns
        all_keys = set()
        for rec in self._buffer:
            all_keys.update(rec.keys())
        columns = {key: [r.get(key) for r in self._buffer] for key in all_keys}
        new_table = pa.Table.from_pydict(columns)

        self._initialize_writer(new_table)
        self._writer.write_table(new_table)
        self._buffer.clear()

    def close(self) -> None:
        """
        Flush buffer, close the ParquetWriter.
        """
        self._flush_buffer()
        if self._writer is not None:
            self._writer.close()
            self._writer = None
