from core import PromptPreparation
from core import PromptQuery
from core import PromptResult
from config import ConfigManager
from utils import TokenizerUtils
from utils.util import get_mongo_url
from storage import HybridHFMongoRepository, HuggingFaceDataHandler, MongoDataHandler, HFExporter


def run_prepare():
    """
    Run the 'prepare' command logic.
    """
    config = ConfigManager()
    tokenizer = TokenizerUtils(tokenizer_path=config.get("tokenizer_path"),
                               max_context_length=config.get("model_max_context_length"),
                               max_generation_length=config.get("model_max_generation_length"))

    repository = HybridHFMongoRepository(
        input_handler=HuggingFaceDataHandler(repo_id=config.get("input_dataset_repo"), split="train", streaming=True),
        pass_handler=MongoDataHandler(
            uri=get_mongo_url(),
            db_name="promptLab",
            collection_name="passedPrompts"
        ),
        fail_handler=MongoDataHandler(
            uri=get_mongo_url(),
            db_name="promptLab",
            collection_name="failedPrompts"
        ),
        stats_handler=MongoDataHandler(
            uri=get_mongo_url(),
            db_name="promptLab",
            collection_name="statistics"
        ),
        exporter=HFExporter(repo_id=config.get("output_dataset_repo")))

    preparer = PromptPreparation(
        repository=repository,
        tokenizer=tokenizer,
        queue_target_size=int(config.get("fetch_prompts_queue_target_size")),
        prompts_queue_name=config.get("fetch_prompts_queue_name"),
        batch_size=int(config.get("batch_size")),
    )
    preparer.run()


def run_query(config):
    """
    Run the 'query' command logic.
    """
    tokenizer = TokenizerUtils(config["model_config"]["tokenizer_path"])
    llm_client = None  # Replace with the actual LLM client initialization

    query_processor = PromptQuery(
        llm_client=llm_client,
        tokenizer=tokenizer,
    )
    batch = []  # Replace with the actual batch input
    query_processor.run(batch)


def run_result(config):
    """
    Run the 'result' command logic.
    """
    repository = None  # Replace with the actual repository initialization
    queue_config = config["prompt_lab"]["queues"]["fetch_prompts_queue"]

    result_processor = PromptResult(
        repository=repository,
        prompts_queue_name=queue_config["name"],
        max_retry=config["prompt_lab"]["max_retry"],
    )
    batch = []  # Replace with the actual batch input
    result_processor.run(batch)
