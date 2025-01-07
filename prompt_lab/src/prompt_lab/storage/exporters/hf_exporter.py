import os
from typing import Iterator, Dict, Any
from huggingface_hub import HfApi, HfFolder
import pandas as pd
from datasets import Dataset
import tempfile
from prompt_lab.utils import logger


class HFExporter:
    """
    Class for exporting data to Hugging Face Hub.
    Supports uploading datasets in chunks and optionally naming the file in the repository.
    """

    def __init__(self, repo_id: str, file_name: str = None, token: str = None, batch_size: int = 1000):
        """
        Initialize the HFExporter.

        Args:
            repo_id (str): The Hugging Face repo ID in the format <user>/<dataset_name>.
            file_name (str, optional): File name for the dataset in the repository.
            token (str, optional): Authentication token for Hugging Face.
            batch_size (int, optional): Number of records to process in each batch. Defaults to 1000.
        """
        self.repo_id = repo_id
        self.file_name = file_name
        self.token = token or HfFolder.get_token()
        if not self.token:
            raise RuntimeError("No Hugging Face token found. Please login with `huggingface-cli login`.")
        self.batch_size = batch_size
        self.api = HfApi()

    def _chunked_generator(self, generator: Iterator[Dict[str, Any]], size: int):
        """
        Yield chunks of data from a generator.

        Args:
            generator (Iterator[Dict[str, Any]]): The record generator.
            size (int): Size of each chunk.
        """
        chunk = []
        for record in generator:
            chunk.append(record)
            if len(chunk) == size:
                yield chunk
                chunk = []
        if chunk:
            yield chunk

    def _save_to_tempfile(self, dataset: Dataset) -> str:
        """
        Save the dataset to a temporary Parquet file.

        Args:
            dataset (Dataset): The Hugging Face dataset to save.

        Returns:
            str: Path to the temporary Parquet file.
        """
        temp_file = tempfile.NamedTemporaryFile(suffix=".parquet", delete=False)
        dataset.to_parquet(temp_file.name)
        logger.debug(f"Dataset saved locally to {temp_file.name}.")
        return temp_file.name

    def _upload_to_hub(self, file_path: str):
        """
        Upload the Parquet file to the Hugging Face Hub.

        Args:
            file_path (str): Path to the Parquet file.
        """
        if not self.file_name:
            raise ValueError("file_name must be specified to upload the file to the repository with its extension.")

        # Ensure the file name has the correct extension
        if not self.file_name.endswith(".parquet"):
            self.file_name += ".parquet"

        logger.info(f"token: {self.token}")
        logger.info(f"Uploading dataset to {self.repo_id} with file name: {self.file_name}.")

        # Upload the file to the repository
        self.api.upload_file(
            path_or_fileobj=file_path,
            path_in_repo=self.file_name,
            repo_id=self.repo_id,
            repo_type="dataset",
            token=self.token,
            commit_message=f"Upload {self.file_name}",
        )
        logger.info(
            f"Dataset uploaded to https://huggingface.co/datasets/{self.repo_id}/blob/main/{self.file_name}")

    def export(self, record_generator: Iterator[Dict[str, Any]]) -> None:
        """
        Export records from a generator to the Hugging Face Hub.

        Args:
            record_generator (Iterator[Dict[str, Any]]): A generator yielding records.
        """
        logger.info("Starting dataset export...")
        full_dataset = None

        for i, batch in enumerate(self._chunked_generator(record_generator, self.batch_size), start=1):
            logger.debug(f"Processing batch {i} with size {len(batch)}.")
            batch_df = pd.DataFrame(batch)
            batch_dataset = Dataset.from_pandas(batch_df)

            if full_dataset is None:
                full_dataset = batch_dataset
            else:
                full_dataset = Dataset.from_pandas(
                    pd.concat([full_dataset.to_pandas(), batch_df], ignore_index=True)
                )

        if full_dataset is None:
            logger.info("No records to export.")
            return

        temp_file_path = self._save_to_tempfile(full_dataset)
        try:
            self._upload_to_hub(temp_file_path)
        finally:
            logger.debug(f"Cleaning up temporary file: {temp_file_path}")
            os.remove(temp_file_path)  # Correctly use os.remove
