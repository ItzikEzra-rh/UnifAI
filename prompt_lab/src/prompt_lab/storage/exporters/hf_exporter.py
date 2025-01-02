"""
hf_exporter.py

Responsible for taking a generator of processed records, converting them to Parquet,
and pushing them to Hugging Face. This is separate from the repository logic,
adhering to SOLID principles.
"""

from typing import Iterator, Dict, Any
from datasets import Dataset
import pandas as pd
import tempfile


class HFExporter:
    """
    This class handles exporting records from a generator to Hugging Face directly
    while efficiently managing memory.
    """

    def __init__(self, repo_id: str, token: str = None, batch_size: int = 1000):
        """
        Initialize the exporter with Hugging Face repository details.

        :param repo_id: The Hugging Face dataset repo to push to (e.g., "user/my_dataset").
        :param token: Optional Hugging Face token for private repos.
        :param batch_size: Number of records to process in a single batch.
        """
        self.repo_id = repo_id
        self.token = token
        self.batch_size = batch_size

    def export(self, record_generator: Iterator[Dict[str, Any]]) -> None:
        """
        Convert the given `record_generator` to batches and push to Hugging Face.

        :param record_generator: A generator yielding dictionaries representing processed data.
        """

        def chunked_generator(generator, size):
            """Yield chunks of data from a generator."""
            chunk = []
            for record in generator:
                chunk.append(record)
                if len(chunk) == size:
                    yield chunk
                    chunk = []
            if chunk:
                yield chunk

        # Process records in chunks
        full_dataset = None

        for i, batch in enumerate(chunked_generator(record_generator, self.batch_size), 1):
            print(f"Processing batch {i}...")
            # Convert the batch to a Pandas DataFrame
            df = pd.DataFrame(batch)

            # Append to the dataset
            dataset = Dataset.from_pandas(df)
            if full_dataset is None:
                full_dataset = dataset
            else:
                full_dataset = Dataset.from_pandas(
                    pd.concat([full_dataset.to_pandas(), df], ignore_index=True)
                )

        if full_dataset is None:
            print("No records to process.")
            return

        # Use a temporary file for the Parquet dataset
        with tempfile.NamedTemporaryFile(suffix=".parquet", delete=True) as tmp_file:
            # Save to Parquet locally in the temp file
            full_dataset.to_parquet(tmp_file.name)
            print(f"Temporary dataset saved to {tmp_file.name}.")

            # Push to Hugging Face
            full_dataset.push_to_hub(self.repo_id, token=self.token)
            print(f"Successfully pushed dataset to https://huggingface.co/{self.repo_id}")
