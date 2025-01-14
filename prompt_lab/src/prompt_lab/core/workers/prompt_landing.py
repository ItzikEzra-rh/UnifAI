from typing import List
from prompt_lab.prompt import Prompt, PromptReviewFailRetry, PromptRetryPolicy, PromptCompositePolicy
from prompt_lab.batch import Batch, BatchCompositeStrategy, BatchRetryPromptsStrategy, BatchPassPromptsStrategy
from prompt_lab.utils.celery.celery import send_task
from prompt_lab.utils import logger
from tqdm import tqdm


class PromptLanding:

    def __init__(
            self,
            repository,
            orbiter_queue_name,
            orbiter_task_name="run_orbiter",
            max_retry=3
    ):
        """
        Initialize PromptLanding with repository, queue details, and retry configurations.

        Args:
            repository: Repository object for managing prompt data.
            orbiter_queue_name: Name of the Celery queue for orbiter tasks.
            orbiter_task_name: Name of the orbiter task to execute.
            max_retry: Maximum retry attempts for a prompt.
        """
        self.repository = repository
        self.max_retry = max_retry
        self.orbiter_queue_name = orbiter_queue_name
        self.orbiter_task_name = orbiter_task_name

        # Define batch strategies and prompt policies
        self.retry_batch = Batch(
            batch_strategies=BatchCompositeStrategy([BatchRetryPromptsStrategy()]),
            prompt_policies=PromptCompositePolicy([
                PromptRetryPolicy(self.max_retry),
                PromptReviewFailRetry(self.max_retry)
            ])
        )
        self.pass_batch = Batch(batch_strategies=BatchCompositeStrategy([BatchPassPromptsStrategy()]))
        self.fail_batch = Batch()

        logger.info("[PromptLanding] Initialized.")

    def refresh_progress_bar(self):
        processed = self.repository.get_processed_num()
        total = self.repository.get_prompts_size()
        progress_bar = tqdm(total=total, desc="Processing Prompts", unit="prompt")

        # Update progress bar
        progress_bar.n = processed
        progress_bar.total = total
        progress_bar.refresh()

    def run(self, batch: List[dict]):
        """
        Process a batch of prompts, classify them into pass, retry, or fail, and take appropriate actions.

        Args:
            batch: List of prompt dictionaries to process.
        """
        # Convert dictionaries to Prompt objects
        prompts = [Prompt.from_dict(**prompt) for prompt in batch]

        logger.info(f"[PromptLanding] processing {len(prompts)} prompts.")
        # Classify prompts into respective batches
        for prompt in prompts:
            (self.retry_batch.add_prompt(prompt) or
             self.pass_batch.add_prompt(prompt) or
             self.fail_batch.add_prompt(prompt))

        # Handle pass batch: Save successful prompts
        if self.pass_batch.has_prompts():
            logger.info(f"[PromptLanding] passed prompts: {self.pass_batch.prompts_count()}.")
            self.repository.save_pass_prompts(self.pass_batch.to_dict())

        # Handle fail batch: Save failed prompts
        if self.fail_batch.has_prompts():
            logger.info(f"[PromptLanding] failed prompts: {self.fail_batch.prompts_count()}.")
            self.repository.save_fail_prompts(self.fail_batch.to_dict())

        # Handle retry batch: Update retry counters and re-queue prompts
        if self.retry_batch.has_prompts():
            logger.info(f"[PromptLanding] retry prompts: {self.retry_batch.prompts_count()}.")
            self.repository.update_retry_counter(self.retry_batch.prompts_count())
            send_task(
                self.orbiter_task_name,
                celery_queue=self.orbiter_queue_name,
                batch=self.retry_batch.to_dict()
            )
            logger.info(
                f"[PromptLanding] Submitted {self.retry_batch.prompts_count()} retry prompts to queue {self.orbiter_queue_name}.")

        self.refresh_progress_bar()

        # Export repository state
        self.repository.export()
