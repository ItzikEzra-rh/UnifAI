from core import PromptLaunchpad, PromptOrbiter, PromptLanding
from config import ConfigManager
from utils import TokenizerUtils
from utils.util import get_mongo_url
from storage import HybridHFMongoRepository, HuggingFaceDataHandler, MongoDataHandler, HFExporter
from llm_client import VLLMClient
from typing import List


def initialize_tokenizer():
    """Initialize and return configuration and tokenizer."""
    config = ConfigManager()
    tokenizer = TokenizerUtils(
        tokenizer_path=config.get("tokenizer_path"),
        max_context_length=config.get("model_max_context_length"),
        max_generation_length=config.get("model_max_generation_length"),
    )
    return tokenizer


def initialize_mongo_handlers(mongo_uri, db_name):
    """Initialize and return MongoDB data handlers."""
    return (
        MongoDataHandler(uri=mongo_uri, db_name=db_name, collection_name="passedPrompts"),
        MongoDataHandler(uri=mongo_uri, db_name=db_name, collection_name="failedPrompts"),
        MongoDataHandler(uri=mongo_uri, db_name=db_name, collection_name="statistics"),
    )


def initialize_repository(config, pass_handler, fail_handler, stats_handler):
    """Initialize and return the repository."""
    return HybridHFMongoRepository(
        input_handler=HuggingFaceDataHandler(
            repo_id=config.get("input_dataset_repo"),
            file_name=config.get("input_dataset_file_name"),
            split="train",
            streaming=True
        ),
        pass_handler=pass_handler,
        fail_handler=fail_handler,
        stats_handler=stats_handler,
        exporter=HFExporter(repo_id=config.get("output_dataset_repo")),
    )


def run_launchpad():
    """
    Run the 'prepare' command logic.
    """
    config = ConfigManager()
    tokenizer = initialize_tokenizer()
    mongo_uri = get_mongo_url()
    db_name = "promptLab"
    pass_handler, fail_handler, stats_handler = initialize_mongo_handlers(mongo_uri, db_name)
    repository = initialize_repository(config, pass_handler, fail_handler, stats_handler)

    PromptLaunchpad(
        repository=repository,
        tokenizer=tokenizer,
        orbiter_task_name=config.get("orbiter_task_name"),
        orbiter_queue_name=config.get("orbiter_queue_name"),
        orbiter_queue_target_size=config.get_as_int("orbiter_queue_target_size"),
        batch_size=config.get_as_int("batch_size"),
    ).run()


def run_orbiter(batch: List[dict]):
    """
    Run the 'query' command logic.
    """
    config = ConfigManager()
    tokenizer = initialize_tokenizer()
    llm_client = VLLMClient(
        api_url=config.get("model_api_url"),
        model_name=config.get("model_name"),
        max_context_length=config.get_as_int("model_max_context_length")
    )

    PromptOrbiter(
        llm_client=llm_client,
        tokenizer=tokenizer,
        review_queue_name=config.get("reviewer_queue_name"),
        reviewer_task_name=config.get("reviewer_task_name")
    ).run(batch)


def run_landing():
    """
    Run the 'result' command logic.
    """
    config = ConfigManager()
    mongo_uri = get_mongo_url()
    db_name = "promptLab"
    pass_handler, fail_handler, stats_handler = initialize_mongo_handlers(mongo_uri, db_name)
    repository = initialize_repository(config, pass_handler, fail_handler, stats_handler)

    result_processor = PromptLanding(
        repository=repository,
        orbiter_queue_name=config.get("orbiter_queue_name"),
        orbiter_task_name=config.get("orbiter_task_name"),
        max_retry=config.get_as_int("max_retry"),
    )

    batch = []  # Replace with the actual batch input
    result_processor.run(batch)
