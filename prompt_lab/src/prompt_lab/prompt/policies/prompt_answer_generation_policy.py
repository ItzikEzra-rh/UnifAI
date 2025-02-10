import random
from .prompt_policy import PromptPolicy
from ..prompt import Prompt
from prompt_lab.utils import logger


class PromptAnswerGenerationPolicy(PromptPolicy):

    def apply(self, prompt: Prompt) -> bool:
        """Apply a retry policy for prompts in question/answer generation states."""
        if not prompt.failed and prompt.is_question_generation_state():
            prompt.question = prompt.current_answer
            print("PromptAnswerGenerationPolicy succeeded")
            return True
        print("PromptAnswerGenerationPolicy failed")
        return False
