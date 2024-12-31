from policies import SkipPolicy
from prompt import Prompt


class PassSkipPolicy(SkipPolicy):
    """
    Example: If prompt.token_count > max_token_limit, skip the prompt and record it in the repository.
    """

    def should_skip(self, prompt: Prompt) -> bool:
        if not prompt.failed:
            print(f"[SkipPolicy] Skipped prompt due to reviewer fail score, uuid: {prompt.uuid}")
            return True
        return False
