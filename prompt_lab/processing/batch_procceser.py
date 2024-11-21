class BatchProcessor:
    """
    BatchProcessor manages batching of prompts based on size and token constraints.
    It tracks the current batch and allows for processing and retrieving batches incrementally.
    """

    def __init__(self, batch_size, tokenizer, skipped_data, io_repository):
        """
        Initializes the BatchProcessor with batching parameters.

        Args:
            batch_size (int): Maximum number of prompts allowed in a single batch.
            tokenizer: Tokenizer instance used for calculating token counts.
            skipped_data (list): List to store skipped prompts.
            io_repository: Repository instance for saving skipped data.
        """
        self.batch_size = batch_size
        self.tokenizer = tokenizer
        self.skipped_data = skipped_data
        self.io_repository = io_repository
        self.token_limit = self.tokenizer.get_toking_limit()
        self.current_batch = []
        self.current_token_count = 0
        self.skipped_elements_count = 0

    def add_prompt(self, prompt):
        """
        Attempts to add a prompt to the current batch. If constraints are exceeded, the prompt is skipped.

        Args:
            prompt (dict): A single prompt with metadata.

        Returns:
            bool: True if the prompt was added successfully, False otherwise.
        """
        prompt_tokens = self.tokenizer.tokenize(prompt["formatted_prompt"])
        prompt["token_count"] = prompt_tokens

        if prompt_tokens > self.token_limit:
            self._skip_due_to_token_size(prompt["metadata"])
            return False

        # Check if adding the prompt exceeds batch constraints
        if self.current_token_count + prompt_tokens > self.token_limit or len(self.current_batch) >= self.batch_size:
            return False

        # Add the prompt to the current batch
        self.current_batch.append(prompt)
        self.current_token_count += prompt_tokens
        return True

    def is_batch_full(self):
        """
        Checks if the current batch is full based on size or token constraints.

        Returns:
            bool: True if the batch is full, False otherwise.
        """
        return len(self.current_batch) >= self.batch_size or self.current_token_count >= self.token_limit

    def finalize_batch(self):
        """
        Finalizes and retrieves the current batch, resetting the internal state.

        Returns:
            list: The finalized batch of prompts.
        """
        finalized_batch = self.current_batch
        self._reset_batch()
        return finalized_batch

    def get_current_batch(self):
        """
        Retrieves the current batch without resetting it.

        Returns:
            list: The current batch of prompts.
        """
        return self.current_batch

    def _reset_batch(self):
        """
        Resets the internal state for the current batch.
        """
        self.current_batch = []
        self.current_token_count = 0

    def _skip_due_to_token_size(self, metadata):
        """
        Handles prompts that exceed token size constraints by marking them as skipped.

        Args:
            metadata (dict): Metadata of the skipped prompt.
        """
        metadata["skip"] = {"reason": "token_size"}
        self.skipped_data.append(metadata)
        self.io_repository.save_skipped_data(self.skipped_data)
        self.skipped_elements_count += 1
        print(f"Skipped prompt due to token size: {metadata.get('element_type')}")

    def get_skipped_count(self):
        """
        Retrieves the total number of skipped prompts.

        Returns:
            int: Count of skipped prompts.
        """
        return self.skipped_elements_count
