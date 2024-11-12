import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from prompt_formatter import PromptFormatter
from config import Config
from logger import logger

import requests
from transformers import AutoTokenizer

class QAScoringSystem:
    """Main class for handling the Q&A scoring system."""

    def __init__(self, config: Config):
        """Initialize the scoring system with configuration."""
        self.config = config
        self.tokenizer = AutoTokenizer.from_pretrained(config.MODEL_NAME)
        self.passed_elements: List[Dict[str, Any]] = []
        self.failed_elements: List[Dict[str, Any]] = []

    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in a given text."""
        tokens = self.tokenizer.encode(text, truncation=False)
        return len(tokens)

    def send_request(self, prompts: List[str]) -> List[str]:
        """Send a batch of prompts to the LLM and return the responses."""
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

    def process_batch(self, batch_prompts: List[str], batch_metadata: List[Dict[str, Any]], 
                     batch_index: int) -> None:
        """Process a batch of prompts and update passed/failed elements."""
        logger.info(f"Processing batch {batch_index + 1} with {len(batch_prompts)} prompts...")
        responses = self.send_request(batch_prompts)

        for meta, response in zip(batch_metadata, responses):
            score = self._parse_score(response)
            self._log_review_summary(meta, response, score)
            self._categorize_element(meta, score)

    def _parse_score(self, response: str) -> int:
        """Parse the response string into a score."""
        try:
            return int(response.strip())
        except ValueError:
            logger.error("Failed to parse response as integer")
            return 0

    def _log_review_summary(self, meta: Dict[str, Any], response: str, score: int) -> None:
        """Log the review summary including question, answer, and score."""
        logger.info("\n--- Review Summary ---")
        logger.info(f"Question:\ninput:\n{meta['input']}\n\noutput:\n{meta['output']}")
        logger.info(f"Answer: {response}")
        logger.info(f"Score: {score}")

    def _categorize_element(self, element: Dict[str, Any], score: int) -> None:
        """Categorize an element as passed or failed based on its score."""
        if score >= self.config.SCORE_THRESHOLD:
            self.passed_elements.append(element)
        else:
            self.failed_elements.append({"element": element, "score": score})

    @staticmethod
    def save_results(elements: List[Dict[str, Any]], file_path: Path) -> None:
        """Save elements to a JSON file."""
        try:
            with file_path.open('w') as f:
                json.dump(elements, f, indent=4)
        except IOError as e:
            logger.error(f"Error saving results to {file_path}: {e}")
            raise

    def process_elements(self, elements: List[Dict[str, Any]]) -> None:
        """Process all elements in batches."""
        batch_prompts: List[str] = []
        batch_metadata: List[Dict[str, Any]] = []
        batch_index = 0
        batch_token_count = 0

        for element in elements:
            prompt = PromptFormatter.create_prompt(element)
            prompt_text = self.tokenizer.apply_chat_template(
                prompt, tokenize=False, add_generation_prompt=True
            )
            prompt_token_count = self.count_tokens(prompt_text)

            if prompt_token_count > self.config.MAX_CONTEXT_LEN - self.config.MAX_TOKENS:
                logger.warning(
                    f"Skipping prompt with {prompt_token_count} tokens as it exceeds max context length."
                )
                self.failed_elements.append({"element": element, "score": None})
                continue

            if (len(batch_prompts) < self.config.BATCH_SIZE_LIMIT and 
                batch_token_count + prompt_token_count <= self.config.MAX_CONTEXT_LEN - self.config.MAX_TOKENS):
                batch_prompts.append(prompt_text)
                batch_metadata.append(element)
                batch_token_count += prompt_token_count
            else:
                self.process_batch(batch_prompts, batch_metadata, batch_index)
                batch_prompts = [prompt_text]
                batch_metadata = [element]
                batch_token_count = prompt_token_count
                batch_index += 1

        # Process remaining prompts in the final batch
        if batch_prompts:
            self.process_batch(batch_prompts, batch_metadata, batch_index)