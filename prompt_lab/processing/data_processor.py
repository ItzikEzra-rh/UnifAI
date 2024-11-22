from llm_client.vllm import VLLMClient
from utils.tokenizer import TokenizerUtils
from processing.prompt_generator import PromptGenerator
from processing.batch_procceser import BatchProcessor
from utils.celery.celery import send_task, is_celery_queue_empty
from time import sleep


class DataProcessor:
    """
    DataProcessor coordinates the processing of prompts by batching them, sending them to an LLM client,
    and managing results and progress tracking.
    """

    def __init__(self, io_repository, project_config, api_url, model_name,
                 max_context_length, max_generation_length, batch_size):
        """
        Initializes DataProcessor with dependencies and configuration.

        Args:
            io_repository: Handles I/O operations for loading/saving data.
            project_config: Dictionary containing project configurations.
            api_url: API URL for the LLM client.
            model_name: Name of the model to use.
            max_context_length: Maximum token length for the prompt context.
            max_generation_length: Maximum token length for generated responses.
            batch_size: Maximum number of prompts per batch.
        """
        self.io_repository = io_repository
        self.tokenizer = TokenizerUtils(model_name, max_context_length=max_context_length,
                                        max_generation_length=max_generation_length)
        self.llm_client = VLLMClient(api_url, model_name, max_context_length)
        self.prompt_generator = PromptGenerator(self.tokenizer, project_config)
        self.skipped_data = self.io_repository.load_skipped_data()
        self.batch_processor = BatchProcessor(batch_size, self.tokenizer, self.skipped_data, self.io_repository)
        self.current_prompt_index = self.io_repository.load_progress()
        self.processed_data = self.io_repository.load_processed_data()
        print("DataProcessor initialized.")

    def process_all_elements(self):
        """Main method to process all elements, batching prompts and sending them to the LLM client."""
        # Generate all prompts and metadata
        for element in self.io_repository.load_data():
            if element["uid"] in self.processed_data:
                continue

            prompts = self.prompt_generator.create_prompts(element_data=element)
            for prompt in prompts:
                if not self.batch_processor.add_prompt(prompt=prompt) and self.batch_processor.is_batch_full():
                    batch = self.batch_processor.finalize_batch()
                    if batch:
                        # send to process batch by prompts process workers
                        while True:
                            if is_celery_queue_empty("prompts_process_queue"):
                                send_task(task_name="fetch_prompts_batch",
                                          celery_queue="prompts_process_queue",
                                          batch=batch)
                                break
                            sleep(2)

    def process_batch(self, batch_prompts, metadata):
        """
        Sends a batch of prompts to the LLM client and processes the responses.

        Args:
            batch_prompts: List of formatted prompts to send in the batch.
            metadata: List of metadata dictionaries for each prompt in the batch.
        """
        print("Sending batch to LLM client.")
        choices = self.llm_client.send_request(batch_prompts, max_tokens=self.tokenizer.max_generation_length)
        print(f"Received {len(choices)} responses from LLM client.")

        # Process each response and metadata entry
        llm_res_batch = []
        for meta, choice in zip(metadata, choices):
            self.print_progress(meta["element_type"], meta["group"], meta["category"], choice["text"])
            element_data = {
                "uid": meta["original_data"]["uid"],
                "input": meta["input_text"],
                "output": choice["text"],
                "element_type": meta["element_type"],
                "group": meta["group"],
                "category": meta["category"],
                "original_data": meta["original_data"]
            }
            llm_res_batch.append(element_data)
        return llm_res_batch

    def skip_due_to_hallucination(self, element_data):
        """
        Adds element data to skipped list due to hallucination and saves to the repository.

        Args:
            element_data: Original data of the element being skipped.
        """
        element_data["skip"] = {"reason": "hallucination"}
        self.skipped_data.append(element_data)
        self.io_repository.save_skipped_data(self.skipped_data)
        print(f"Element skipped due to hallucination: {element_data.get('element_type')}")

    def print_progress(self, element_type, group_name, category, output):
        """
        Prints the progress of the current processing element in a stylized format.

        Args:
            element_type: Type of the element being processed.
            group_name: Group of the element.
            category: Category of the element.
            output: Generated output from the LLM client.
        """
        separator = "=" * 80
        print(separator)
        print(f"Processing Element {self.current_prompt_index + 1}".center(80))
        print(f"Element Type: {element_type} | Group: {group_name} | Category: {category}".center(80))
        print(separator)
        print(f"\n{output}\n")
        print(separator)

# TODO is this the best way to check the celery queue?
# TODO check processed and uid test
# TODO make sure code works as expected
# TODO indexing with print
# TODO Flask?
