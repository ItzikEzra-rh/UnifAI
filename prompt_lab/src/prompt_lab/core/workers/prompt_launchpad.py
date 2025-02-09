import time
from prompt_lab.prompt import PromptGenerator, PromptMaxTokenSizeFailPolicy, PromptCompositePolicy
from prompt_lab.batch import BatchMaxPromptsNumberStrategy, BatchMaxTokenStrategy, BatchCompositeStrategy, Batch
from prompt_lab.utils.celery.celery import is_queue_full, send_task
from prompt_lab.utils.tokenizer import TokenizerUtils
from prompt_lab.storage import DataRepository
from prompt_lab.utils import logger
from tqdm import tqdm


class PromptLaunchpad:
    """
    Handles the enqueuing of prompts into a processing queue.
    """

    def __init__(
            self,
            repository: DataRepository,
            tokenizer: TokenizerUtils,
            orbiter_queue_target_size: int,
            orbiter_queue_name: str,
            batch_size: int = 8,
            orbiter_task_name: str = "run_orbiter",
    ):
        """
        Initialize PromptPreparation with the given parameters.
        """
        self.repository = repository
        self.tokenizer = tokenizer
        self.orbiter_queue_target_size = orbiter_queue_target_size
        self.orbiter_queue_name = orbiter_queue_name
        self.batch_size = batch_size
        self.orbiter_task_name = orbiter_task_name

        self.generator = PromptGenerator(self.repository)
        self.prepared_prompts_batch = Batch(
            batch_strategies=BatchCompositeStrategy(
                [
                    BatchMaxTokenStrategy(self.tokenizer.get_tokens_limit()),
                    BatchMaxPromptsNumberStrategy(self.batch_size),
                ]
            ),
            prompt_policies=PromptCompositePolicy(
                [PromptMaxTokenSizeFailPolicy(self.tokenizer.get_tokens_limit())]
            ),
        )
        self.processed_uuids = self.repository.load_prompts_uuids()

        logger.info("[PromptLaunchpad] Initialized.")

    def run(self):
        """
        Process prompts, apply policies and strategies, and enqueue them for submission.
        """
        self.generator.set_number_of_elements_and_prompts()

        for prompt in tqdm(self.generator,
                           total=self.repository.get_prompts_size(),
                           desc="Processing Prompts"):
            if prompt.uuid in self.processed_uuids:
                continue  # Skip already processed prompts

            if self._process_prompt(prompt):
                continue

        # Submit remaining prompts
        if self.prepared_prompts_batch.has_prompts():
            logger.info(
                f"[PromptPreparation] submitting batch with the remaining {self.prepared_prompts_batch.prompts_count()} prompts.")
            self._submit_batch()

    def _process_prompt(self, prompt) -> bool:
        """
        Process an individual prompt.

        Args:
            prompt: The prompt to process.

        Returns:
            bool: True if the prompt is successfully processed, False otherwise.
        """
        if self.prepared_prompts_batch.add_prompt(prompt):
            return True

        # Handle blocked batch
        if self.prepared_prompts_batch.is_blocked:
            self._submit_batch()

        # Handle failed prompts
        if prompt.is_failed:
            self.repository.save_fail_prompts([prompt.to_dict()])
            return False

        # Retry adding to a new batch
        return self.prepared_prompts_batch.add_prompt(prompt)

    def _submit_batch(self):
        """
        Finalize and submit the current batch of prompts.
        """
        if not self.prepared_prompts_batch.has_prompts():
            return
        logger.debug(f"batch prompt count {self.prepared_prompts_batch.prompts_count()}")
        logger.debug(f"batch token count {self.prepared_prompts_batch.batch_token_size()}")

        finalized_prompts = self.prepared_prompts_batch.finalize_batch()

        while is_queue_full(queue_name=self.orbiter_queue_name, queue_target_size=self.orbiter_queue_target_size):
            logger.debug(f"[PromptPreparation] Queue full. Retrying in 5 seconds...")
            time.sleep(5)

        send_task(
            self.orbiter_task_name,
            celery_queue=self.orbiter_queue_name,
            batch=finalized_prompts,
        )
        logger.debug(
            f"[PromptPreparation] Submitted {len(finalized_prompts)} prompts to queue {self.orbiter_queue_name}.")
