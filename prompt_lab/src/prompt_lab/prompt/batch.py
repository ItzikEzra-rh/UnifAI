import copy
from typing import List
from prompt import Prompt
from strategies import CompositeBatchStrategy
from policies import CompositeRetryPolicy, CompositeSkipPolicy


class Batch:
    """
    Maintains a list of Prompt objects.
    Decides if it can add a Prompt using a BatchStrategy,
    and defers skip logic to a SkipPolicy.
    """

    def __init__(self,
                 batch_strategies: CompositeBatchStrategy = CompositeBatchStrategy([]),
                 skip_policies: CompositeSkipPolicy = CompositeSkipPolicy([]),
                 retry_policies: CompositeRetryPolicy = CompositeRetryPolicy([])):
        self.batch_strategies = batch_strategies
        self.skip_policies = skip_policies
        self.retry_policies = retry_policies
        self.prompts: List[Prompt] = []

    def add_prompt(self, prompt: Prompt) -> bool:
        """
        1) Check if skip_policy wants to skip the prompt.
        2) If not skipped, apply retry policy if exist
        3) see if batch_strategy allows adding it.
        """
        if not self.skip_policies.should_skip(prompt) and self.retry_policies.apply_retry(
                prompt) and self.batch_strategies.can_add_prompt(current_batch=self.prompts, new_prompt=prompt):
            self.add_prompt(prompt)
            return True
        return False

    def finalize_batch(self) -> List[Prompt]:
        """
        Return a copy of the prompts for submission, then reset internally.
        """
        finalized = copy.deepcopy(self.prompts)
        self.prompts.clear()
        return finalized

    def to_dict(self):
        return [prompt.to_dict() for prompt in self.prompts]

    def has_prompts(self) -> bool:
        return len(self.prompts) > 0
