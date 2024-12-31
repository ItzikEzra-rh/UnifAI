from typing import List
from prompt import Prompt, Batch
from policies import RetryPolicy, CompositeRetryPolicy, SkipPolicy, CompositeSkipPolicy
from utils.tokenizer import TokenizerUtils


class PromptQuery:
    """
    Handles the process of querying an LLM with a batch of prompts.

    Responsibilities:
      - Fetch prompts from a queue and send them to an LLM for responses.
      - Apply retry and skip policies to manage prompts dynamically.
      - Process and handle LLM responses.

    Attributes:
      - llm_client: The client used to communicate with the LLM.
      - retry_policies: A composite of retry policies applied to prompts.
      - skip_policies: A composite of skip policies applied to prompts.
      - tokenizer: Utility for tokenizing and managing token limits.
      - batch: A collection of prompts managed with retry and skip policies.
    """

    def __init__(
            self,
            llm_client,
            retry_policies: List[RetryPolicy],
            skip_policies: List[SkipPolicy],
            tokenizer: TokenizerUtils
    ):
        """
        Initializes the PromptQuery instance.

        Args:
            llm_client: The LLM client used to send requests.
            retry_policies (List[RetryPolicy]): List of retry policies to handle prompt retries.
            skip_policies (List[SkipPolicy]): List of skip policies to manage prompt exclusions.
            tokenizer (TokenizerUtils): Utility for handling tokenization and token limits.
        """
        self.llm_client = llm_client
        self.retry_policies = CompositeRetryPolicy(retry_policies)
        self.skip_policies = CompositeSkipPolicy(skip_policies)
        self.tokenizer = tokenizer
        self.batch = Batch(retry_policies=self.retry_policies, skip_policies=self.skip_policies)

        print("[PromptQuery] Initialized.")

    def run(self, batch: List[dict]):
        """
        Processes a batch of prompts and queries the LLM for responses.

        Args:
            batch (List[dict]): A list of dictionaries representing prompts to process.
                                Each dictionary is converted to a `Prompt` object.

        Workflow:
            - Converts dictionaries in the batch to `Prompt` objects.
            - Adds prompts to the batch for management by policies.
            - Sends formatted prompts to the LLM for response generation.
            - Updates each prompt with the LLM's output text.

        Returns:
            Batch: The batch object containing processed prompts with their responses.
        """
        for prompt_dict in batch:
            prompt = Prompt.from_dict(**prompt_dict)
            self.batch.add_prompt(prompt)

        formatted_prompts = [prompt.formatted_prompt for prompt in self.batch.to_dict()]
        choices = self.llm_client.send_request(formatted_prompts, max_tokens=self.tokenizer.max_generation_length)

        # Process each response and update the prompts in the batch
        for prompt, choice in zip(self.batch.prompts, choices):
            prompt.output_text = choice["text"]

        return self.batch
