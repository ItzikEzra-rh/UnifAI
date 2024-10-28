class BatchProcessor:
    """
    BatchProcessor is responsible for managing batching logic, ensuring that prompts
    are grouped into batches that meet specified constraints for size and token limits.
    """

    def __init__(self, batch_size, tokenizer, skipped_data, io_repository):
        """
        Initializes the BatchProcessor with batching parameters.

        Args:
            batch_size (int): The maximum number of prompts allowed in a single batch.
            token_limit (int): The maximum token count allowed for a batch.
        """
        self.batch_size = batch_size
        self.tokenizer = tokenizer
        self.skipped_data = skipped_data
        self.io_repository = io_repository
        self.token_limit = self.tokenizer.get_toking_limit()

    def create_batch(self, all_prompts, prompts_count, start_index):
        """
        Creates a batch of prompts from the provided list starting at the specified index.

        Args:
            all_prompts (list): A list of all available prompts, each with metadata.
            prompts_count (int): The total number of prompts available.
            start_index (int): The starting index in `all_prompts` from which to begin batching.

        Returns:
            tuple: A tuple containing two lists:
                - batch_prompts (list): The prompts selected for the batch.
                - metadata (list): The corresponding metadata for each prompt in the batch.

        Notes:
            - The batch will contain prompts until either the batch size limit or token limit is reached.
            - Batching stops if adding another prompt would exceed either the batch size or token count limits.
        """
        batch_prompts = []
        metadata = []
        total_token_count = 0

        for i in range(start_index, prompts_count):
            prompt_info = all_prompts[i]

            prompt_tokens = self.tokenizer.tokenize(prompt_info["formatted_prompt"])
            prompt_info["metadata"]["token_count"] = prompt_tokens

            # Skip if prompt exceeds token limit
            if prompt_tokens > self.token_limit:
                self.skip_due_to_big_token_size(element_data=prompt_info["metadata"])

            # Check if adding this prompt would exceed batch size or token limit
            if len(batch_prompts) >= self.batch_size or (total_token_count + prompt_tokens > self.token_limit):
                break

            # Add prompt and update metadata and token count
            batch_prompts.append(prompt_info["formatted_prompt"])
            metadata.append(prompt_info["metadata"])
            total_token_count += prompt_tokens

        return batch_prompts, metadata, total_token_count

    def skip_due_to_big_token_size(self, element_data):
        """
        Adds element data to skipped list due to hallucination and saves to the repository.

        Args:
            element_data: Original data of the element being skipped.
        """
        element_data["skip"] = {"reason": "token_size"}
        self.skipped_data.append(element_data)
        self.io_repository.save_skipped_data(self.skipped_data)
        print(
            f"Element {element_data.get('element_type')} skipped due to big token size {element_data.get('token_count')}")
