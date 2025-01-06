from .prompt_policy import PromptPolicy
from prompt import Prompt
from utils import logger


class PromptMaxTokenSizeFailPolicy(PromptPolicy):
    """
    Example: If prompt.token_count > max_token_limit, skip the prompt and record it in the repository.
    """

    def __init__(self, max_token_limit: int):
        self.max_token_limit = max_token_limit

    def apply(self, prompt: Prompt) -> bool:
        if prompt.token_count > self.max_token_limit:
            prompt.failed = True
            prompt.set_fail_reason("MaxTokenSizeFailPolicy")
            logger.info(
                f"[MaxTokenSizeFailPolicy] failed prompt due to token size {prompt.token_count}, uuid: {prompt.uuid}")
            return True
        return False
