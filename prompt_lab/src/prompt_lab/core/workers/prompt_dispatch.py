from typing import List
from prompt import Prompt, Batch
from policies import PassSkipPolicy, FailSkipPolicy, CompositeSkipPolicy
from utils.celery.celery import send_task


class PromptDispatch:

    def __init__(
            self,
            repository,
            prompts_queue_name
    ):
        self.repository = repository
        self.passed_batch = Batch(skip_policies=CompositeSkipPolicy([FailSkipPolicy()]))
        self.fail_batch = Batch(skip_policies=CompositeSkipPolicy([PassSkipPolicy()]))
        self.prompts_queue_name = prompts_queue_name
        self.prompt_query_task_name: str = "fetch_prompts_batch"

        print("[PromptDispatch] Initialized.")

    def run(self, batch: List[dict]):
        for prompt in batch:
            prompt = Prompt.from_dict(**prompt)
            self.passed_batch.add_prompt(prompt)
            self.fail_batch.add_prompt(prompt)

        if self.passed_batch.has_prompts():
            self.repository.save_processed_data(self.passed_batch.to_dict())
            self.repository.save_progress([{"uuid": prompt.uuid} for prompt in self.passed_batch.prompts])

        if self.fail_batch.has_prompts():
            send_task(self.prompt_query_task_name,
                      celery_queue=self.prompts_queue_name,
                      batch=self.fail_batch.to_dict())
