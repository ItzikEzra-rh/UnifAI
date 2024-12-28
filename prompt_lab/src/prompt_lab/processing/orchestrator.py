from typing import List
from prompt import Prompt, Batch, PromptGenerator
from policies import RetryPolicy


class Orchestrator:
    """
    The main coordinator:
      - Iterates over PromptGenerator for the next prompt
      - Uses a Batch to add prompts (with skip & strategy constraints)
      - Submits the batch to a queue when full
      - Provides a method to handle LLM results, applying a RetryPolicy
    """

    def __init__(
            self,
            repository,
            project_config,
            tokenizer,
            llm_client,
            batch_strategy,
            skip_policy,
            retry_policy: RetryPolicy,
            batch_size: int,
            queue_target_size: int,
            queue_name: str
    ):
        self.repository = repository
        self.project_config = project_config
        self.tokenizer = tokenizer
        self.llm_client = llm_client

        self.batch_strategy = batch_strategy
        self.skip_policy = skip_policy
        self.retry_policy = retry_policy
        self.batch_size = batch_size

        self.queue_target_size = queue_target_size
        self.queue_name = queue_name

        self.generator = PromptGenerator(self.repository, self.tokenizer, self.project_config)
        self.batch = Batch(self.batch_strategy, self.skip_policy, self.repository)

        # Track processed
        self.processed_uuids = set()
        for item in self.repository.load_progress():
            self.processed_uuids.add(item["uuid"])

        print("[Orchestrator] Initialized.")

    def run(self):
        """
        Main loop: read prompts from generator, add to batch, submit when full, continue.
        """
        count = 0
        for prompt in self.generator:
            if prompt.uuid in self.processed_uuids:
                # Already processed
                continue

            added = self.batch.add_prompt(prompt)
            if not added:
                # If the batch is full or skip triggered
                if self.batch.has_prompts():
                    self._submit_current_batch()
                self.batch = Batch(self.batch_strategy, self.skip_policy, self.repository)
                # Attempt to re-add (in case skip policy didn't skip)
                if not self.skip_policy.should_skip(prompt):
                    self.batch.add_prompt(prompt)

            count += 1
            if count % 100 == 0:
                print(f"[Orchestrator] Processed {count} prompts...")

        # leftover
        if self.batch.has_prompts():
            self._submit_current_batch()

        print(f"[Orchestrator] All prompts processed. Total: {count}")

    def _submit_current_batch(self):
        finalized_prompts = self.batch.finalize_batch()
        if not finalized_prompts:
            return

        # while get_queue_length_rabbitmq(self.queue_name) >= self.queue_target_size:
        #     time.sleep(5)

        payload = [p.to_dict() for p in finalized_prompts]
        # send_task("fetch_prompts_batch", celery_queue=self.queue_name, batch=payload)
        print(f"[Orchestrator] Submitted {len(finalized_prompts)} prompts to queue {self.queue_name}.")

    def process_llm_results(self, prompt_dicts: List[dict], responses: List[dict]):
        """
        Called by a Celery worker after LLM has responded.
        Each item in prompt_dicts matches an item in responses by index.
        """
        for prompt_data, resp in zip(prompt_dicts, responses):
            prompt_obj = Prompt(
                uuid=prompt_data["uuid"],
                formatted_prompt=prompt_data["formatted_prompt"],
                token_count=prompt_data["token_count"],
                metadata=prompt_data["metadata"]
            )
            text = resp.get("text", "")
            # QA check
            if not self._is_response_valid(text):
                # Attempt retry
                can_retry = self.retry_policy.apply_retry_logic(prompt_obj)
                if can_retry:
                    # re-queue the prompt
                    # send_task("fetch_prompts_batch", self.queue_name, batch=[prompt_obj.to_dict()])
                    pass
                else:
                    self.repository.save_skipped_data({
                        "uuid": prompt_obj.uuid,
                        "metadata": prompt_obj.metadata,
                        "reason": prompt_obj.metadata.get("skip", {}).get("reason", "")
                    })
            else:
                # success
                self._save_processed_result(prompt_obj, text)

    def _is_response_valid(self, text: str) -> bool:
        """Stub for QA logic. Return True if text is considered valid."""
        return bool(text.strip())

    def _save_processed_result(self, prompt: Prompt, output_text: str):
        record = {
            "uuid": prompt.uuid,
            "input": prompt.metadata.get("input_text"),
            "output": output_text,
            "element_type": prompt.metadata.get("element_type"),
            "group": prompt.metadata.get("group"),
            "category": prompt.metadata.get("category"),
            "validation": prompt.metadata.get("validation"),
            "original_data": prompt.metadata.get("original_data")
        }
        self.repository.save_processed_data(record)
        self.repository.save_progress(prompt.uuid)
        self.processed_uuids.add(prompt.uuid)
        print(f"[Orchestrator] Saved processed prompt {prompt.uuid}.")
