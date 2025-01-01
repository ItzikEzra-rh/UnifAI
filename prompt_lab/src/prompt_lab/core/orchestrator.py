from typing import List
from prompt import Prompt, Batch, PromptGenerator
from policies import RetryPolicy


class Orchestrator:


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



        print("[Orchestrator] Initialized.")


