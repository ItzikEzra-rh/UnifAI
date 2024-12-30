from typing import List
from .retry_policy import RetryPolicy
from prompt import Prompt


class CompositeRetryPolicy(RetryPolicy):
    """
    A composite retry policy that applies multiple RetryPolicy instances.
    """

    def __init__(self, policies: List[RetryPolicy]):
        self.policies = policies

    def apply_retry_logic(self, prompt: Prompt) -> bool:
        """
        Return True only if all policies agree that the prompt should be retried.
        """
        for policy in self.policies:
            if not policy.apply_retry_logic(prompt):
                return False
        return True
