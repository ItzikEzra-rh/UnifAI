import copy
from typing import List
from prompt import Prompt
from strategies import BatchStrategy, CompositeBatchStrategy
from policies import CompositeRetryPolicy, CompositeSkipPolicy
from policies import SkipPolicy


class Batch:
    """
    Maintains a list of Prompt objects.
    Decides if it can add a Prompt using a BatchStrategy,
    and defers skip logic to a SkipPolicy.
    """

    def __init__(self, batch_strategies: CompositeBatchStrategy, skip_policies: CompositeSkipPolicy, repository):
        self.batch_strategies = batch_strategies
        self.skip_policies = skip_policies
        self.repository = repository
        self.prompts: List[Prompt] = []

    def add_prompt(self, prompt: Prompt) -> bool:
        """
        1) Check if skip_policy wants to skip the prompt.
        2) If not skipped, see if batch_strategy allows adding it.
        """
        if self.skip_policies.should_skip(prompt):
            return False
        if not self.batch_strategies.can_add_prompt(current_batch=self.prompts, new_prompt=prompt):
            return False

        self.add_prompt(prompt)
        return True

    def finalize_batch(self) -> List[Prompt]:
        """
        Return a copy of the prompts for submission, then reset internally.
        """
        finalized = copy.deepcopy(self.prompts)
        self.prompts.clear()
        return finalized

    def has_prompts(self) -> bool:
        return len(self.prompts) > 0
