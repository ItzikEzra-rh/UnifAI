from core import PromptLaunchpad, PromptOrbiter, PromptLanding
from config import ConfigManager
from utils import TokenizerUtils
from utils.util import get_mongo_url
from storage import HybridHFMongoRepository, HuggingFaceDataHandler, MongoDataHandler, HFExporter


def run_launchpad():
    """
    Run the 'prepare' command logic.
    """
    # Initialize configuration and tokenizer
    config = ConfigManager()
    tokenizer = TokenizerUtils(
        tokenizer_path=config.get("tokenizer_path"),
        max_context_length=config.get("model_max_context_length"),
        max_generation_length=config.get("model_max_generation_length"),
    )

    # Define common MongoDB connection details
    mongo_uri = get_mongo_url()
    db_name = "promptLab"

    # Initialize data handlers
    pass_handler = MongoDataHandler(uri=mongo_uri, db_name=db_name, collection_name="passedPrompts")
    fail_handler = MongoDataHandler(uri=mongo_uri, db_name=db_name, collection_name="failedPrompts")
    stats_handler = MongoDataHandler(uri=mongo_uri, db_name=db_name, collection_name="statistics")

    # Initialize repository
    repository = HybridHFMongoRepository(
        input_handler=HuggingFaceDataHandler(
            repo_id=config.get("input_dataset_repo"), split="train", streaming=True
        ),
        pass_handler=pass_handler,
        fail_handler=fail_handler,
        stats_handler=stats_handler,
        exporter=HFExporter(repo_id=config.get("output_dataset_repo")),
    )

    # Initialize and run preparer
    preparer = PromptLaunchpad(
        repository=repository,
        tokenizer=tokenizer,
        queue_target_size=config.get_as_int("fetch_prompts_queue_target_size"),
        prompts_queue_name=config.get("fetch_prompts_queue_name"),
        batch_size=config.get_as_int("batch_size"),
    )

    preparer.run()


def run_orbiter(config):
    """
    Run the 'query' command logic.
    """
    tokenizer = TokenizerUtils(config["model_config"]["tokenizer_path"])
    llm_client = None  # Replace with the actual LLM client initialization

    query_processor = PromptOrbiter(
        llm_client=llm_client,
        tokenizer=tokenizer,
    )
    batch = []  # Replace with the actual batch input
    query_processor.run(batch)


def run_landing(config):
    """
    Run the 'result' command logic.
    """
    repository = None  # Replace with the actual repository initialization
    queue_config = config["prompt_lab"]["queues"]["fetch_prompts_queue"]

    result_processor = PromptLanding(
        repository=repository,
        prompts_queue_name=queue_config["name"],
        max_retry=config["prompt_lab"]["max_retry"],
    )
    batch = []  # Replace with the actual batch input
    result_processor.run(batch)
