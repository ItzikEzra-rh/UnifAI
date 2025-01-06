from typing import List
from prompt import Prompt
from batch import Batch
from utils import TokenizerUtils, logger
from utils.celery.celery import send_task


class PromptOrbiter:
    """
    Handles the process of querying an LLM with a batch of prompts.

    Responsibilities:
      - Fetch prompts from a queue and send them to an LLM for responses.
      - Apply retry and skip policies to manage prompts dynamically.
      - Process and handle LLM responses.

    Attributes:
      - llm_client: The client used to communicate with the LLM.
      - retry_policies: A composite of retry policies applied to prompts.
      - skip_policies: A composite of skip policies applied to prompts.
      - tokenizer: Utility for tokenizing and managing token limits.
      - batch: A collection of prompts managed with retry and skip policies.
    """

    def __init__(
            self,
            llm_client,
            tokenizer: TokenizerUtils,
            review_queue_name: str,
            reviewer_task_name: str,
            reviewed_prompts_queue_name: str,
            landing_task_name: str,
            reviewer: bool

    ):
        """
        Initializes the PromptQuery instance.

        Args:
            llm_client: The LLM client used to send requests.
            tokenizer (TokenizerUtils): Utility for handling tokenization and token limits.
        """
        self.llm_client = llm_client
        self.tokenizer = tokenizer
        self.review_queue_name = review_queue_name
        self.reviewer_task_name = reviewer_task_name
        self.reviewed_prompts_queue_name = reviewed_prompts_queue_name
        self.landing_task_name = landing_task_name
        self.reviewer = reviewer
        self.batch = Batch()

        logger.info("[PromptQuery] Initialized.")

    def run(self, batch: List[dict]):
        """
        Processes a batch of prompts and queries the LLM for responses.

        Args:
            batch (List[dict]): A list of dictionaries representing prompts to process.
                                Each dictionary is converted to a `Prompt` object.

        Workflow:
            - Converts dictionaries in the batch to `Prompt` objects.
            - Adds prompts to the batch for management by policies.
            - Sends formatted prompts to the LLM for response generation.
            - Updates each prompt with the LLM's output text.

        Returns:
            Batch: The batch object containing processed prompts with their responses.
        """
        logger.info(f"Received batch of size {len(batch)}.")
        for prompt_dict in batch:
            prompt = Prompt.from_dict(**prompt_dict)
            self.batch.add_prompt(prompt)

        formatted_prompts = [prompt.formatted_prompt for prompt in self.batch.prompts]
        choices = self.llm_client.send_request(formatted_prompts, max_tokens=self.tokenizer.max_generation_length)

        # Process each response and update the prompts in the batch
        for prompt, choice in zip(self.batch.prompts, choices):
            prompt.output_text = choice["text"]

        finalized_prompts = self.batch.finalize_batch()

        send_queue_name = self.review_queue_name if self.reviewer else self.reviewed_prompts_queue_name
        send_task_name = self.reviewer_task_name if self.reviewer else self.landing_task_name
        send_task(
            task_name=send_task_name,
            celery_queue=send_queue_name,
            batch=finalized_prompts,
        )
        logger.info(
            f"[PromptPreparation] Submitted {len(finalized_prompts)} prompts to queue {send_queue_name},task {send_task_name}.")
