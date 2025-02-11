from typing import List
from prompt_lab.prompt import Prompt, PromptCompositePolicy, PromptStatePolicy, PromptMaxTokenSizeFailPolicy
from prompt_lab.batch import BatchMaxTokenStrategy, BatchCompositeStrategy, Batch
from prompt_lab.utils import TokenizerUtils, logger
from prompt_lab.utils.celery.celery import send_task
from prompt_lab.storage import DataRepository


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
            repository: DataRepository,
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
        self.repository = repository
        self.tokenizer = tokenizer
        self.review_queue_name = review_queue_name
        self.reviewer_task_name = reviewer_task_name
        self.reviewed_prompts_queue_name = reviewed_prompts_queue_name
        self.landing_task_name = landing_task_name
        self.reviewer = reviewer
        self.query_batch = Batch(prompt_policies=PromptCompositePolicy([PromptStatePolicy(tokenizer=self.tokenizer),
                                                                        PromptMaxTokenSizeFailPolicy(
                                                                            self.tokenizer.get_tokens_limit())]),
                                 batch_strategies=BatchCompositeStrategy(
                                     [BatchMaxTokenStrategy(self.tokenizer.get_tokens_limit())]
                                 ))

        logger.info("[PromptOrbiter] Initialized.")

    def _process_prompt(self, prompt) -> bool:
        """
        Process an individual prompt.

        Args:
            prompt: The prompt to process.

        Returns:
            bool: True if the prompt is successfully processed, False otherwise.
        """
        if self.query_batch.add_prompt(prompt):
            return True

        # Handle blocked batch
        if self.query_batch.is_blocked:
            self.inference_batch()

        # Handle failed prompts
        if prompt.is_failed:
            self.repository.save_fail_prompts([prompt.to_dict()])
            return False

        # Retry adding to a new batch
        return self.query_batch.add_prompt(prompt)

    def inference_batch(self):
        if not self.query_batch.has_prompts():
            return

        logger.debug(f"batch prompt count {self.query_batch.prompts_count()}")
        logger.info(f"[PromptOrbiter] Inferencing batch of size {self.query_batch.prompts_count()}.")
        formatted_prompts = [prompt.formatted_chat_prompt for prompt in self.query_batch.prompts]
        choices = self.llm_client.send_request(formatted_prompts, max_tokens=self.tokenizer.max_generation_length)

        # Process each response and update the prompts in the batch
        for prompt, choice in zip(self.query_batch.prompts, choices):
            prompt.current_answer = choice["text"]
            self.log_question_answer(prompt)
        finalized_prompts = self.query_batch.finalize_batch()

        send_queue_name = self.review_queue_name if self.reviewer else self.reviewed_prompts_queue_name
        send_task_name = self.reviewer_task_name if self.reviewer else self.landing_task_name
        send_task(
            task_name=send_task_name,
            celery_queue=send_queue_name,
            batch=finalized_prompts,
        )
        logger.info(
            f"[PromptOrbiter] Submitted {len(finalized_prompts)} prompts to queue {send_queue_name},task {send_task_name}.")

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
        logger.info(f"[PromptOrbiter] Received batch of size {len(batch)}.")
        for prompt_dict in batch:
            prompt = Prompt.from_dict(**prompt_dict)
            self._process_prompt(prompt)

        if self.query_batch.has_prompts():
            self.inference_batch()

    @staticmethod
    def log_question_answer(prompt):
        """Logs the current question and answer in a structured, visually appealing format with colors."""

        # ANSI color codes
        GREEN = "\033[92m"
        BLUE = "\033[94m"
        RESET = "\033[0m"  # Reset color

        separator = "═" * 80  # Stylish separator
        question_header = f"{GREEN}🟢 QUESTION {RESET}".center(80, "═")
        answer_header = f"{BLUE}🔵 ANSWER {RESET}".center(80, "═")

        logger.info(f"\n{separator}\n{question_header}\n{separator}\n")
        logger.info(f"{GREEN}{prompt.current_question}{RESET}\n")
        logger.info(f"\n{separator}\n{answer_header}\n{separator}\n")
        logger.info(f"{BLUE}{prompt.current_answer}{RESET}\n")
        logger.info(f"\n{separator}\n")
