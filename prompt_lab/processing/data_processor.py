from llm_client.vllm import VLLMClient
from utils.tokenizer import TokenizerUtils
from processing.prompt_generator import PromptGenerator
from processing.batch_procceser import BatchProcessor


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
        print(f"Loaded {len(self.processed_data)} processed records and {len(self.skipped_data)} skipped records.")
        print(f"Resuming from prompt index: {self.current_prompt_index}")

    def process_all_elements(self):
        """Main method to process all elements, batching prompts and sending them to the LLM client."""
        data = self.io_repository.load_data()
        print(f"Loaded {len(data)} elements for processing.")

        # Generate all prompts and metadata
        all_prompts = [prompt for element_data in data for prompt in self.prompt_generator.create_prompts(element_data)]
        prompts_count = len(all_prompts)
        print(f"Total prompts generated: {prompts_count}")

        # Process prompts in batches, starting from the last saved index
        while self.current_prompt_index < prompts_count:
            print(f"Processing from prompt index: {self.current_prompt_index}")
            batch_prompts, metadata, total_token_count, skipped_elements_count = self.batch_processor.create_batch(
                all_prompts,
                prompts_count,
                self.current_prompt_index)

            self.current_prompt_index += skipped_elements_count
            if not batch_prompts:
                continue
            print(f"Created batch with {len(batch_prompts)} prompts. batch tokens size is {total_token_count}")

            # Process the batch and update progress
            self.process_batch(batch_prompts, metadata)
            self.current_prompt_index += len(batch_prompts)
            self.io_repository.save_progress(self.current_prompt_index)
            print(f"Progress saved at prompt index: {self.current_prompt_index}")

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
        for meta, choice in zip(metadata, choices):
            if choice.get("finish_reason", "").strip() == "length":
                print(f"Skipping due to hallucination for element: {meta['element_type']}")
                self.skip_due_to_hallucination(meta["original_data"])
            else:
                self.save_processed_data(meta, choice["text"])

    def save_processed_data(self, meta, response_text):
        """
        Saves a single processed prompt's metadata and response.

        Args:
            meta: Metadata for the processed prompt.
            response_text: Generated response from the LLM client.
        """
        element_data = {
            "input": meta["input_text"],
            "output": response_text,
            "element_type": meta["element_type"],
            "group": meta["group"],
            "category": meta["category"],
            "original_data": meta["original_data"]
        }
        self.processed_data.append(element_data)
        self.io_repository.save_processed_data(self.processed_data)
        print(f"Processed data saved for element type: {meta['element_type']}")
        self.print_progress(meta["element_type"], meta["group"], meta["category"], response_text)

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

