import json
import requests

from pathlib import Path
from typing import Any, Dict, List
from transformers import AutoTokenizer

from logger import logger
from g_eval.config import EvalMetric, Config
from g_eval.g_eval_prompt_formatter import GEvalPromptFormatter
from g_eval.g_eval_scorer import GEvalScorer

class GEvalQASystem:
    """Main class for GEval-based Q&A evaluation system."""

    def __init__(self, config: Config):
        """Initialize the evaluation system."""
        self.config = config
        self.tokenizer = AutoTokenizer.from_pretrained(config.MODEL_NAME)
        self.passed_elements: List[Dict[str, Any]] = []
        self.failed_elements: List[Dict[str, Any]] = []

    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return len(self.tokenizer.encode(text, truncation=False))

    def send_request(self, prompts: List[str]) -> List[str]:
        """Send prompts to LLM and get responses."""
        try:
            data = {
                "model": self.config.MODEL_NAME,
                "prompt": prompts,
                "max_tokens": self.config.MAX_TOKENS,
                "temperature": 0.3
            }
            response = requests.post(
                self.config.API_URL,
                json=data,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            response.raise_for_status()
            return [choice["text"] for choice in sorted(
                response.json().get("choices", []),
                key=lambda x: x.get("index", 0)
            )]
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending request to LLM: {e}")
            raise

    def evaluate_element(self, element: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate a single element using all criteria."""
        scores: Dict[EvalMetric, float] = {}
        
        for criterion in self.config.GEVAL_CONFIG.criteria:
            prompt = GEvalPromptFormatter.format_chat_prompt(criterion, element)
            prompt_text = self.tokenizer.apply_chat_template(
                prompt, tokenize=False, add_generation_prompt=True
            )
            
            if self.count_tokens(prompt_text) > self.config.MAX_CONTEXT_LEN - self.config.MAX_TOKENS:
                logger.warning(f"Prompt too long for criterion {criterion.metric}")
                scores[criterion.metric] = criterion.min_score
                continue
                
            response = self.send_request([prompt_text])[0]
            scores[criterion.metric] = GEvalScorer.parse_score(response, criterion)
            
        final_score = GEvalScorer.aggregate_scores(scores, self.config.GEVAL_CONFIG)
        
        return {
            "element": element,
            "criterion_scores": scores,
            "final_score": final_score
        }

    def process_elements(self, elements: List[Dict[str, Any]]) -> None:
        """Process all elements with GEval evaluation."""
        for element in elements:
            try:
                evaluation = self.evaluate_element(element)
                self._categorize_evaluation(evaluation)
                self._log_evaluation(evaluation)
            except Exception as e:
                logger.error(f"Error processing element: {e}")
                self.failed_elements.append({
                    "element": element,
                    "error": str(e)
                })

    def _categorize_evaluation(self, evaluation: Dict[str, Any]) -> None:
        """Categorize evaluation results as passed or failed."""
        if evaluation["final_score"] >= self.config.SCORE_THRESHOLD:
            self.passed_elements.append(evaluation["element"])
        else:
            self.failed_elements.append(evaluation)

    def _log_evaluation(self, evaluation: Dict[str, Any]) -> None:
        """Log evaluation results."""
        logger.info("\n--- Evaluation Summary ---")
        logger.info(f"Element: {evaluation['element'].get('name', 'unnamed')}")
        logger.info(f"Criterion Scores: {evaluation['criterion_scores']}")
        logger.info(f"Final Score: {evaluation['final_score']}")

    @staticmethod
    def save_results(elements: List[Dict[str, Any]], file_path: Path) -> None:
        """Save evaluation results to file."""
        try:
            with file_path.open('w') as f:
                json.dump(elements, f, indent=4)
        except IOError as e:
            logger.error(f"Error saving results to {file_path}: {e}")
            raise