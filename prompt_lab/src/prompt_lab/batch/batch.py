# my_project/processing/batch.py

import copy
from typing import List
from models.prompt import Prompt
from strategies.batch_strategy import BatchStrategy
from policies.skip_policy import SkipPolicy


class Batch:
    """
    Maintains a list of Prompt objects.
    Decides if it can add a Prompt using a BatchStrategy,
    and defers skip logic to a SkipPolicy.
    """

    def __init__(self, batch_strategy: BatchStrategy, skip_policy: SkipPolicy, repository):
        self.batch_strategy = batch_strategy
        self.skip_policy = skip_policy
        self.repository = repository  # can be used if we need to log anything
        self.prompts: List[Prompt] = []

    def add_prompt(self, prompt: Prompt) -> bool:
        """
        1) Check if skip_policy wants to skip the prompt.
        2) If not skipped, see if batch_strategy allows adding it.
        """
        if self.skip_policy.should_skip(prompt):
            return False

        if self.batch_strategy.can_add_prompt(self.prompts, prompt):
            self.prompts.append(prompt)
            return True
        return False

    def finalize_batch(self) -> List[Prompt]:
        """
        Return a copy of the prompts for submission, then reset internally.
        """
        finalized = copy.deepcopy(self.prompts)
        self.prompts.clear()
        return finalized

    def has_prompts(self) -> bool:
        return len(self.prompts) > 0
