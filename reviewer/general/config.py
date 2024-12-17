from dataclasses import dataclass
from pathlib import Path

@dataclass
class Config:
    """Configuration parameters for the Q&A scoring system."""
    INPUT_FILE_PATH: Path = Path("data/Cluster_Infra_Mapping_5_processed.json")
    PASSED_FILE_PATH: Path = Path("data/passed.json")
    FAILED_FILE_PATH: Path = Path("data/failed.json")
    API_URL: str = "http://0.0.0.0:8000/v1/completions"
    MODEL_NAME: str = "meta-llama/Llama-3.1-8B-Instruct"
    BATCH_SIZE_LIMIT: int = 8
    MAX_TOKENS: int = 2
    MAX_CONTEXT_LEN: int = 8192
    SCORE_THRESHOLD: int = 7

    def __post_init__(self):
        """Ensure paths exist."""
        self.INPUT_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        self.PASSED_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        self.FAILED_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)