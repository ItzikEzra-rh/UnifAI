# my_project/factory/orchestrator_factory.py

import os
from config.manager import config
from storage import HybridHFMongoRepository
from utils.tokenizer import TokenizerUtils
from llm_client.vllm import VLLMClient

from policies.skip_policy import TokenSizeSkipPolicy
from policies.retry_policy import SimpleRetryPolicy
from strategies.max_size_and_token_batch_strategy import MaxSizeAndTokenBatchStrategy
from core.orchestrator import Orchestrator

def create_orchestrator() -> Orchestrator:
    # 1) Build repository
    # For example, if you're using a HybridHFMongoRepository:
    repository = HybridHFMongoRepository(...)  # your constructor & config

    # 2) Load project config
    template_path = (
        os.path.join(
            config.get("templates.dir_path"),
            config.get("templates.agent"),
            f"{config.get('templates.type')}.json"
        )
        if not config.get("templates.path")
        else config.get("templates.path")
    )
    from utils.util import load_json_config
    project_config = load_json_config(template_path)

    # 3) Build tokenizer & LLM client
    tokenizer = TokenizerUtils(
        model_name=config.get('model_config.model_name'),
        max_context_length=config.get('model_config.max_context_length'),
        max_generation_length=config.get('model_config.max_generation_length')
    )
    llm_client = VLLMClient(
        api_url=config.get("model_config.api_url"),
        model_name=config.get("model_config.model_name"),
        max_context_length=config.get("model_config.max_context_length")
    )

    # 4) Build strategies/policies
    token_limit = tokenizer.get_toking_limit()
    skip_policy = TokenSizeSkipPolicy(token_limit, repository)
    retry_policy = SimpleRetryPolicy(max_retries=3)
    batch_strategy = MaxSizeAndTokenBatchStrategy(
        max_prompts=config.get('prompt_lab.batch_size'),
        max_total_tokens=token_limit
    )

    # 5) Create orchestrator
    orchestrator = Orchestrator(
        repository=repository,
        project_config=project_config,
        tokenizer=tokenizer,
        llm_client=llm_client,
        batch_strategy=batch_strategy,
        skip_policy=skip_policy,
        retry_policy=retry_policy,
        batch_size=config.get('prompt_lab.batch_size'),
        queue_target_size=config.get('prompt_lab.queues.fetch_prompts_queue.target_size'),
        queue_name=config.get('prompt_lab.queues.fetch_prompts_queue.name')
    )

    return orchestrator
