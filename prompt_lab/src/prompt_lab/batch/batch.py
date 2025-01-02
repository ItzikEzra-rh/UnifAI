import copy
from typing import List
from prompt import Prompt
from strategies import BatchCompositeStrategy
from prompt import CompositePolicy


class Batch:
    """
    Maintains a list of Prompt objects.
    Decides if it can add a Prompt using a BatchStrategy,
    and defers skip logic to a SkipPolicy.
    """

    def __init__(self,
                 batch_strategies: BatchCompositeStrategy = BatchCompositeStrategy([]),
                 prompt_policies: CompositePolicy = CompositePolicy([])):
        self.batch_strategies = batch_strategies
        self.prompt_policies = prompt_policies
        self.prompts: List[Prompt] = []

    def add_prompt(self, prompt: Prompt) -> bool:
        """
        1) apply policies on prompt
        2) apply batch strategies on new prompt
        """
        self.prompt_policies.apply(prompt)
        if self.batch_strategies.apply(self.prompts, prompt):
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

    def to_dict(self):
        return [prompt.to_dict() for prompt in self.prompts]

    def has_prompts(self) -> bool:
        return len(self.prompts) > 0

    def prompts_count(self):
        return len(self.prompts)
