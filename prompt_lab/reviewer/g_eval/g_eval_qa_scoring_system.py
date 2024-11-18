import json
import requests

from pathlib import Path
from typing import Any, Dict, List
from transformers import AutoTokenizer

from logger import logger
from g_eval.config import EvalMetric, Config, GEvalConfig
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


from deepeval import evaluate
from deepeval.metrics import Accuracy, Relevance, Completeness
from deepeval.test_case import LLMTestCase
from transformers import AutoTokenize

class DeepEvalQASystem:
    """Q&A evaluation system using DeepEval library."""

    def __init__(self, config: GEvalConfig):
        """Initialize the evaluation system."""
        self.config = config
        self.metrics = [
            Accuracy(threshold=0.7),
            Relevance(threshold=0.7),
            Completeness(threshold=0.7)
        ]
        
        # Custom model configuration for DeepEval
        # Note: This requires proper setup in DeepEval configuration
        self.model_config = {
            "model": self.config.MODEL_NAME,
            "type": "local",  # or "api" depending on your setup
            "parameters": {
                "temperature": 0.3,
                "max_tokens": 4
            }
        }

    def create_test_case(self, element: Dict[str, Any]) -> LLMTestCase:
        """Create a DeepEval test case from an element."""
        original_data = element.get("original_data", {})
        
        # Format context
        context = (
            f"Here is detailed information about the {element['element_type']} "
            f"{original_data.get('name', 'unnamed')}:\n\n"
            f"{original_data.get('file_location', 'No location provided')}\n\n"
            f"{original_data.get('package', 'No package information')}\n\n"
            f"{original_data.get('imports', 'No imports')}\n\n"
            f"{original_data.get('global_vars', 'No global variables')}\n\n"
            f"Code for {element['element_type']} {original_data.get('name', 'unnamed')}: \n"
            f"```go\n{original_data.get('code', 'No code provided')}\n```"
        )

        return LLMTestCase(
            input=element.get("input", ""),
            actual_output=element.get("output", ""),
            context=context,
            metadata={
                "element_type": element.get("element_type", ""),
                # "group": element.get("group", ""),
                # "category": element.get("category", "")
            }
        )

    async def evaluate_element(self, element: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate a single element using DeepEval metrics."""
        test_case = self.create_test_case(element)
        
        try:
            # Run evaluation with all metrics
            results = await evaluate(
                test_case,
                metrics=self.metrics,
                model=self.model_config
            )
            
            # Calculate average score across all metrics
            total_score = sum(result.score for result in results)
            avg_score = total_score / len(results)
            
            return {
                "element": element,
                "scores": {
                    metric.__class__.__name__: result.score
                    for metric, result in zip(self.metrics, results)
                },
                "final_score": avg_score,
                "passed": avg_score >= self.config.SCORE_THRESHOLD
            }
            
        except Exception as e:
            logger.error(f"Evaluation failed: {e}")
            return {
                "element": element,
                "error": str(e),
                "passed": False
            }

    async def process_elements(self, elements: List[Dict[str, Any]]) -> None:
        """Process all elements with DeepEval evaluation."""
        passed_elements = []
        failed_elements = []

        for element in elements:
            result = await self.evaluate_element(element)
            if result.get("passed", False):
                passed_elements.append(result)
            else:
                failed_elements.append(result)
            self._log_evaluation(result)

        # Save results
        self._save_results(passed_elements, self.config.PASSED_FILE_PATH)
        self._save_results(failed_elements, self.config.FAILED_FILE_PATH)

        logger.info(
            f"Evaluation complete. {len(passed_elements)} elements passed and "
            f"{len(failed_elements)} elements failed."
        )

    def _log_evaluation(self, evaluation: Dict[str, Any]) -> None:
        """Log evaluation results."""
        logger.info("\n--- Evaluation Summary ---")
        logger.info(f"Element: {evaluation['element'].get('original_data', {}).get('name', 'unnamed')}")
        if "scores" in evaluation:
            logger.info(f"Scores: {evaluation['scores']}")
            logger.info(f"Final Score: {evaluation['final_score']}")
        if "error" in evaluation:
            logger.info(f"Error: {evaluation['error']}")

    @staticmethod
    def _save_results(elements: List[Dict[str, Any]], file_path: Path) -> None:
        """Save evaluation results to file."""
        try:
            with file_path.open('w') as f:
                json.dump(elements, f, indent=4)
        except IOError as e:
            logger.error(f"Error saving results to {file_path}: {e}")
            raise