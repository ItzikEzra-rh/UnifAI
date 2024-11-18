import json
import requests

from pathlib import Path
from typing import Any, Dict, List, Tuple
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

from abc import ABC, abstractmethod
from deepeval.test_case import LLMTestCase
from deepeval.metrics import BaseMetric
from transformers import AutoTokenizer

# Initialize the tokenizer
tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-3.1-8B-Instruct")

# Create our own base model class
class BaseLLMModel(ABC):
    """Base class for LLM models."""
    
    @abstractmethod
    async def generate(self, prompt: str) -> str:
        """Generate text from the model."""
        pass


class VLLMModel(BaseLLMModel):
    """Custom VLLM model implementation."""
    
    def __init__(self, api_url: str = "http://0.0.0.0:8000/v1/completions"):
        self.api_url = api_url
        
    async def generate(self, messages: List[Dict[str, str]]) -> str:
        """Generate text using local VLLM service with chat format."""
        try:
            data = {
                "model": "meta-llama/Llama-3.1-8B-Instruct",
                "prompt": messages,
                "max_tokens": 6,
                "temperature": 0.3
            }
            response = requests.post(self.api_url, json=data, headers={"Content-Type": "application/json"})
            response.raise_for_status()
            return response.json()["choices"][0]["text"]
        except Exception as e:
            logger.error(f"VLLM API call failed: {e}")
            raise

class CustomAnswerRelevancyMetric(BaseMetric):
    """Custom implementation of answer relevancy metric using VLLM."""
    def __init__(self, threshold: float = 0.7, model: BaseLLMModel = None):
        self.threshold = threshold
        self.model = model or VLLMModel()
        self.reason = None
        self.score = 0.0
    
    @property
    def name(self) -> str:
        return "Answer Relevancy"
    
    async def _evaluate(self, test_case: LLMTestCase) -> Dict[str, Any]:
        """Evaluate the relevancy of the answer using the VLLM model."""
        prompt = self._create_evaluation_prompt(test_case)
        prompt_text = tokenizer.apply_chat_template(prompt, tokenize=False, add_generation_prompt=True)
        
        try:
            response = await self.model.generate(prompt)
            
            # Extract score from response
            try:
                score_line = response.split('\n')[0]
                score_value = float(score_line)  # Expecting just a number from 1-10
                # Convert 1-10 score to 0-1 range
                self.score = score_value / 10.0
                self.reason = f"Model provided score: {score_value}/10"
                
                # Ensure score is between 0 and 1
                self.score = max(0.0, min(1.0, self.score))
                
            except (ValueError, IndexError) as e:
                logger.error(f"Error parsing model response: {e}")
                self.score = 0.0
                self.reason = f"Error parsing response: {str(e)}"
                
        except Exception as e:
            logger.error(f"Error during measurement: {e}")
            self.score = 0.0
            self.reason = f"Error during measurement: {str(e)}"
        
        return {
            "score": self.score,
            "reason": self.reason
        }
    
    def _create_evaluation_prompt(self, test_case: LLMTestCase) -> List[Dict[str, str]]:
        """Create a prompt for evaluating answer relevancy in chat format."""
        system_message = (
            "You are a reviewer. Rate the output based on the following criteria, using a scale from 1 to 10. "
            "Respond with only a single number from 1 to 10, with no additional text or punctuation.\n\n"
            "Relevance: Assess how well the output addresses the input request. A high score reflects a strong, "
            "meaningful connection between the input and output.\n\n"
            "Absence of Hallucinations: Ensure the output does not contain irrelevant or invented information. "
            "This includes:\n"
            "- Repetitive phrases or nonsensical strings\n"
            "- Incomplete or trailing sentences\n"
            "- Sections of text that do not contribute meaningfully to the requested answer\n"
            "Any presence of hallucinated content should result in a failing score.\n\n"
            "Quality: Evaluate the clarity, coherence, and completeness of the output."
        )

        evaluation_content = (
            f"Context: {test_case.context}\n"
            f"Question: {test_case.input}\n"
            f"Answer: {test_case.actual_output}\n\n"
            f"Your score (1-10):"
        )

        return [
            {"role": "system", "content": system_message},
            {"role": "user", "content": evaluation_content}
        ]

class DeepEvalQASystem:
    """Q&A evaluation system using DeepEval library with VLLM."""

    def __init__(self, config: GEvalConfig):
        """Initialize the evaluation system."""
        self.config = config
        self.vllm_model = VLLMModel(api_url=config.VLLM_API_URL)
        # Initialize metrics with custom VLLM model
        self.metrics = [
            CustomAnswerRelevancyMetric(threshold=0.7, model=self.vllm_model),
        ]

    def create_test_case(self, element: Dict[str, Any]) -> LLMTestCase:
        """Create a DeepEval test case from an element."""
        original_data = element.get("original_data", {})
        
        context = [
            f"Information about {element['element_type']} "
            f"{original_data.get('name', 'unnamed')}:\n\n"
            f"Location: {original_data.get('file_location', 'No location provided')}\n"
            f"Package: {original_data.get('package', 'No package information')}\n"
            f"Imports: {original_data.get('imports', 'No imports')}\n"
            f"Global Variables: {original_data.get('global_vars', 'No global variables')}\n\n"
            f"Code:\n```go\n{original_data.get('code', 'No code provided')}\n```"
        ]

        return LLMTestCase(
            input=element.get("input", ""),
            actual_output=element.get("output", ""),
            context=context
        )

    async def evaluate_element(self, element: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate a single element using DeepEval metrics."""
        test_case = self.create_test_case(element)
        
        try:
            # Run evaluation with all metrics
            results = []
            for metric in self.metrics:
                result = await metric._evaluate(test_case)
                results.append(result)
            
            # Calculate average score
            total_score = sum(result["score"] for result in results)
            avg_score = total_score / len(results)
            
            return {
                "element": element,
                "scores": {
                    f"Metric_{i}": result
                    for i, result in enumerate(results)
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