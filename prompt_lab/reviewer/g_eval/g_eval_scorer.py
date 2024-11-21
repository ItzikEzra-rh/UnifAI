from reviewer.g_eval.config import EvalCriterion, GEvalConfig, EvalMetric
from typing import Any, Dict, List, Optional, Union
from logger import logger

class GEvalScorer:
    """Handles scoring logic for GEval-based evaluation."""

    @staticmethod
    def parse_score(response: str, criterion: EvalCriterion) -> float:
        """Parse and validate the score from LLM response."""
        try:
            score = float(response.strip())
            return max(criterion.min_score, 
                      min(criterion.max_score, score))
        except ValueError:
            logger.error(f"Failed to parse score from response: {response}")
            return criterion.min_score

    @staticmethod
    def aggregate_scores(scores: Dict[EvalMetric, float], 
                        config: GEvalConfig) -> float:
        """Aggregate multiple criterion scores into a final score."""
        if config.aggregation_method == "weighted_average":
            total_weight = sum(c.weight for c in config.criteria)
            weighted_sum = sum(
                scores.get(c.metric, c.min_score) * c.weight 
                for c in config.criteria
            )
            return weighted_sum / total_weight if total_weight > 0 else 0.0
        
        raise ValueError(f"Unsupported aggregation method: {config.aggregation_method}")