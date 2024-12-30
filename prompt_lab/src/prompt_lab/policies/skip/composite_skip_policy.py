from typing import List
from .skip_policy import SkipPolicy
from prompt import Prompt


class CompositeSkipPolicy(SkipPolicy):
    """
    A composite skip policy that applies multiple SkipPolicy instances.
    """

    def __init__(self, policies: List[SkipPolicy]):
        self.policies = policies

    def should_skip(self, prompt: Prompt) -> bool:
        """
        Return True if any policy decides the prompt should be skipped.
        """
        for policy in self.policies:
            if policy.should_skip(prompt):
                return True
        return False
