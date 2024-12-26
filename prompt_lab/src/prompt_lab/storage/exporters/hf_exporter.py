"""
hf_exporter.py

Responsible for taking a list of processed records, converting them to Parquet,
and pushing them to Hugging Face. This is separate from the repository logic,
adhering to SOLID principles.
"""

import pyarrow as pa
import pyarrow.parquet as pq
from typing import List, Dict, Any
from datasets import Dataset


class HFExporter:
    """
    This class handles exporting a list of records (dicts) to a local Parquet file
    and optionally uploading to Hugging Face.
    """

    def export_records_to_hf(
            self,
            records: List[Dict[str, Any]],
            repo_id: str,
            local_parquet_path: str,
            token: str = None
    ) -> None:
        """
        Convert the given `records` to an Arrow table, write Parquet, and push to HF Hub.

        :param records: A list of dictionaries representing processed data.
        :param repo_id: The Hugging Face dataset repo to push to (e.g., "user/my_dataset").
        :param local_parquet_path: Path to write the Parquet file locally.
        :param token: Optional Hugging Face token for private repos.
        """
        if not records:
            print("No records to export.")
            return

        # 1) Convert to Arrow table
        all_keys = set()
        for record in records:
            all_keys.update(record.keys())
        columns = {k: [doc.get(k) for doc in records] for k in all_keys}
        table = pa.Table.from_pydict(columns)

        # 2) Write to local Parquet
        pq.write_table(table, local_parquet_path)
        print(f"Saved {len(records)} records to {local_parquet_path}.")

        # 3) Push to Hugging Face
        ds = Dataset.from_parquet(local_parquet_path)
        ds.push_to_hub(repo_id, token=token)
        print(f"Successfully pushed dataset to https://huggingface.co/{repo_id}")
