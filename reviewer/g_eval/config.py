from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum
from typing import List

class EvalMetric(Enum):
    """Evaluation metrics supported by the system."""
    ACCURACY = "accuracy"
    RELEVANCE = "relevance"
    COMPLETENESS = "completeness"
    CONSISTENCY = "consistency"

@dataclass
class EvalCriterion:
    """Represents a single evaluation criterion."""
    metric: EvalMetric
    prompt_template: str
    weight: float = 1.0
    min_score: float = 0.0
    max_score: float = 100.0

    def format_prompt(self, **kwargs) -> str:
        """Format the prompt template with provided arguments."""
        return self.prompt_template.format(**kwargs)


@dataclass
class GEvalConfig:
    """Configuration for GEval-based evaluation."""
    criteria: List[EvalCriterion] = field(default_factory=list)
    aggregation_method: str = "weighted_average"
    
    @classmethod
    def default_config(cls) -> 'GEvalConfig':
        """Create default GEval configuration with standard criteria."""
        return cls(criteria=[
            EvalCriterion(
                metric=EvalMetric.ACCURACY,
                prompt_template=(
                    # "Rate from 1 to 100 how accurately the following 'Provided Output' answers the given 'Question', "
                    "Rate from 1 to 100 how accurately the following 'Provided Output' answers the given 'Validation Question', "
                    "considering all the provided 'Context'.\n\n"
                    "Context:\n{input_context}\n\n"
                    "Question:\n{question}\n\n"
                    "Validation Question:\n{validation_question}\n\n"
                    "Provided Output:\n{provided_output}\n\n"
                    # "Base your rating on: {validation_question}"
                    "Provide only a number between 1 and 100 representing how accurately the output answers the question based on the given context."
                ),
                weight=1.0
            ),
            # Add more criteria as needed
        ])

@dataclass
class Config:
    """System configuration parameters."""
    INPUT_FILE_PATH: Path = Path("data/openshift-qe-dataset.json")
    PASSED_FILE_PATH: Path = Path("data/passed.json")
    FAILED_FILE_PATH: Path = Path("data/failed.json")
    API_URL: str = "http://0.0.0.0:8000/v1/completions"
    MODEL_NAME: str = "meta-llama/Llama-3.1-8B-Instruct"
    BATCH_SIZE_LIMIT: int = 8
    MAX_TOKENS: int = 4
    MAX_CONTEXT_LEN: int = 16384
    SCORE_THRESHOLD: float = 70.0
    GEVAL_CONFIG: GEvalConfig = field(default_factory=GEvalConfig.default_config)

    def __post_init__(self):
        """Ensure paths exist."""
        for path in [self.INPUT_FILE_PATH.parent, self.PASSED_FILE_PATH.parent, self.FAILED_FILE_PATH.parent]:
            path.mkdir(parents=True, exist_ok=True)

################################################################################################################
@dataclass
class GEvalConfig:
    """Configuration parameters."""
    INPUT_FILE_PATH: Path = Path("data/openshift-qe-dataset.json")
    PASSED_FILE_PATH: Path = Path("data/passed.json")
    FAILED_FILE_PATH: Path = Path("data/failed.json")
    VLLM_API_URL: str = "http://0.0.0.0:8000/v1/completions"
    # MODEL_NAME: str = "meta-llama/Llama-3.1-8B-Instruct"
    SCORE_THRESHOLD: float = 0.7  # 70% threshold