from typing import List
from prompt import Prompt, PromptReviewFailRetry, PromptRetryPolicy, PromptCompositePolicy
from batch import Batch, BatchCompositeStrategy, BatchRetryPromptsStrategy, BatchPassPromptsStrategy
from utils.celery.celery import send_task


class PromptResult:

    def __init__(
            self,
            repository,
            prompts_queue_name,
            max_retry=3
    ):
        self.repository = repository
        self.max_retry = max_retry
        self.prompts_queue_name = prompts_queue_name
        self.retry_batch = Batch(batch_strategies=BatchCompositeStrategy([BatchRetryPromptsStrategy()]),
                                 prompt_policies=PromptCompositePolicy([PromptRetryPolicy(self.max_retry),
                                                                        PromptReviewFailRetry(self.max_retry)]))
        self.pass_batch = Batch(batch_strategies=BatchCompositeStrategy([BatchPassPromptsStrategy()]))
        self.fail_batch = Batch()
        self.prompt_query_task_name: str = "fetch_prompts_batch"

        print("[PromptDispatch] Initialized.")

    def run(self, batch: List[dict]):
        prompts = [Prompt.from_dict(**prompt) for prompt in batch]
        for prompt in prompts:
            (self.retry_batch.add_prompt(prompt) or
             self.pass_batch.add_prompt(prompt) or
             self.fail_batch.add_prompt(prompt))

        if self.pass_batch.has_prompts():
            self.repository.save_pass_prompts(self.pass_batch.to_dict())

        if self.retry_batch.has_prompts():
            self.repository.update_retry_counter(self.retry_batch.prompts_count())
            send_task(self.prompt_query_task_name,
                      celery_queue=self.prompts_queue_name,
                      batch=self.retry_batch.to_dict())

        self.repository.export()
