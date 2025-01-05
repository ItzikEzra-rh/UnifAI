from typing import List
from prompt import Prompt, PromptCompositePolicy
from .strategies import BatchCompositeStrategy


class Batch:
    """
    Maintains a list of Prompt objects.
    Decides if it can add a Prompt using BatchStrategies,
    and apply Prompt Policies to prompts.
    """

    def __init__(
            self,
            batch_strategies: BatchCompositeStrategy = BatchCompositeStrategy([]),
            prompt_policies: PromptCompositePolicy = PromptCompositePolicy([]),
    ):
        self.batch_strategies = batch_strategies
        self.prompt_policies = prompt_policies
        self.prompts: List[Prompt] = []
        self._blocked = False

    def add_prompt(self, prompt: Prompt) -> bool:
        """
        Adds a prompt to the batch if it passes policies and strategies.

        - Applies policies to the prompt.
        - Checks batch strategies for adding the prompt.
        - If some strategy is a blocker and it didn't apply, then sets the batch to a blocked state.
        """
        if self.is_blocked:
            return False

        self.prompt_policies.apply(prompt)

        if self.batch_strategies.apply(self.prompts, prompt):
            self.prompts.append(prompt)
            return True

        self._blocked = self.batch_strategies.is_blocker(self.prompts, prompt)
        return False

    def finalize_batch(self) -> List[dict]:
        """
        Finalizes and clears the batch, returning the prompts.
        """
        finalized = self.to_dict()
        self.prompts.clear()
        self._blocked = False
        return finalized

    def to_dict(self) -> List[dict]:
        """
        Converts all prompts in the batch to a list of dictionaries.
        """
        return [prompt.to_dict() for prompt in self.prompts]

    def has_prompts(self) -> bool:
        """
        Checks if the batch contains any prompts.
        """
        return bool(self.prompts)

    def prompts_count(self) -> int:
        """
        Returns the count of prompts in the batch.
        """
        return len(self.prompts)

    def batch_token_size(self) -> int:
        """
        Returns the batch token size
        """
        return sum([prompt.token_count for prompt in self.prompts])

    @property
    def is_blocked(self) -> bool:
        """
        Indicates if the batch is currently blocked.
        """
        return self._blocked
