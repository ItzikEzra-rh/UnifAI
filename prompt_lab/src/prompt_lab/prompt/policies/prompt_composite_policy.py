from typing import List
from .prompt_policy import PromptPolicy
from prompt import Prompt


class PromptCompositePolicy(PromptPolicy):
    """
    A composite skip policy that applies multiple SkipPolicy instances.
    """

    def __init__(self, policies: List[PromptPolicy]):
        self.policies = policies

    def apply(self, prompt: Prompt) -> bool:
        """
        Return True if any policy decides the prompt should be skipped.
        """
        for policy in self.policies:
            if policy.apply(prompt):
                return True
        return False
