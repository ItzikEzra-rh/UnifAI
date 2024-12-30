from typing import List
from prompt import Batch, PromptGenerator
from policies import CompositeSkipPolicy, SkipPolicy
from strategies import CompositeBatchStrategy, BatchStrategy
from utils.celery.celery import is_queue_full, send_task
from utils.tokenizer import TokenizerUtils
import time


class PromptEnqueue:
    """
    The main responsibility:
      - Iterates over PromptGenerator for the next prompt
      - Uses a Batch to add prompts (with skip & strategy constraints)
      - Submits the batch to a queue when full
    """

    def __init__(
            self,
            repository,
            tokenizer: TokenizerUtils,
            batch_strategies: List[BatchStrategy],
            skip_policies: List[SkipPolicy],
            queue_target_size: int,
            prompts_queue_name: str,
            prompt_query_task_name: str = "fetch_prompts_batch"
    ):
        self.repository = repository
        self.tokenizer = tokenizer
        self.prompt_query_task_name = prompt_query_task_name
        self.batch_strategies = CompositeBatchStrategy(batch_strategies)
        self.skip_policies = CompositeSkipPolicy(skip_policies)

        self.queue_target_size = queue_target_size
        self.prompts_queue_name = prompts_queue_name

        self.generator = PromptGenerator(self.repository, self.tokenizer)
        self.batch = Batch(self.batch_strategies, self.skip_policies, self.repository)

        # Track processed, a set of UUIDs, optimized for search O(1)
        self.processed_uuids = self.repository.load_progress()

        print("[PromptEnqueue] Initialized.")

    def run(self):
        """
        Main loop: read prompts from generator, add to batch, submit when full, continue.
        """

        for prompt in self.generator:
            if prompt.uuid in self.processed_uuids:
                # Already processed
                continue

            added = self.batch.add_prompt(prompt)
            if not added:
                # If the batch is full or skip triggered
                if self.batch.has_prompts():
                    self._submit_current_batch()

                # Attempt to re-add (in case skip policy didn't skip)
                if not self.skip_policies.should_skip(prompt):
                    self.batch.add_prompt(prompt)

        # leftover
        if self.batch.has_prompts():
            self._submit_current_batch()

    def _submit_current_batch(self):
        finalized_prompts = self.batch.finalize_batch()
        if not finalized_prompts:
            return

        while is_queue_full(queue_name=self.prompts_queue_name, queue_target_size=self.queue_target_size):
            # print(f"[Orchestrator] Queue {self.queue_name} is full. Retrying in 5 seconds...")
            time.sleep(5)

        payload = [p.to_dict() for p in finalized_prompts]
        send_task(self.prompt_query_task_name, celery_queue=self.prompts_queue_name, batch=payload)

        print(f"[Orchestrator] Submitted {len(finalized_prompts)} prompts to queue {self.prompts_queue_name}.")
