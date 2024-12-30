from typing import List
from prompt import Prompt
from policies import RetryPolicy, CompositeRetryPolicy
from utils.tokenizer import TokenizerUtils


class PromptQuery:
    """
    The main responsibility:
      - Fetch prompts prompts Queue and query LLM for a response
      - Provides a method to handle LLM results, applying a RetryPolicy
    """

    def __init__(
            self,
            llm_client,
            retry_policies: List[RetryPolicy],
            queue_name: str,
            tokenizer: TokenizerUtils
    ):
        self.llm_client = llm_client
        self.retry_policies = CompositeRetryPolicy(retry_policies)
        self.queue_name = queue_name
        self.tokenizer = tokenizer

        print("[PromptQuery] Initialized.")

    def run(self, batch: List[dict]):
        """
        Called by a Celery worker after a prompt is enqueued to prompt queue.
        Each item in batch matches an item in responses by index.
        """
        prompts = []
        for prompt_dict in batch:
            prompt = Prompt.from_dict(prompt_dict)
            if prompt.is_failed:
                CompositeRetryPolicy.apply_retry_logic(prompt) # TODO retry make new variation of prompt, add skip policy for retry exceeded

            prompts.append()

        formatted_prompts = [prompt.formatted_prompt for prompt in prompts]
        choices = self.llm_client.send_request(formatted_prompts, max_tokens=self.tokenizer.max_generation_length)

        # Process each response and metadata entry
        llm_res_batch = []
        for prompt, choice in zip(prompts, choices):
            prompt.output = choice["text"]


