from .prompt_policy import PromptPolicy
from ..prompt import Prompt
import random
from prompt_lab.utils import logger


class PromptStatePolicy(PromptPolicy):

    def __init__(self, tokenizer):
        self.tokenizer = tokenizer

    def apply(self, prompt: Prompt) -> bool:
        """applies a prompt based on available data."""

        if prompt.question and prompt.answer:
            return False  # No changes needed

        if prompt.is_question_generation_state():
            prompt.current_question = prompt.question_seed
            prompt.current_system_message = prompt.seed_system_message
            prompt.current_validation = prompt.question_validation
        elif prompt.is_answer_generation_state():
            prompt.current_question = random.choice(prompt.question_options) if prompt.question_options else prompt.question
            prompt.current_system_message = prompt.question_system_message
            prompt.current_validation = prompt.answer_validation
        else:
            # TODO add a state if output exist and needs a question
            return False  # No changes needed

        prompt.formatted_chat_prompt = self.tokenizer.format_chat_prompt([
            {"role": "system", "content": prompt.current_system_message},
            # {"role": "context", "content": prompt.context},
            {"role": "user", "content": f"**context** {prompt.context} \n**user** {prompt.current_question}"}
        ])
        prompt.token_count = self.tokenizer.count_tokens(prompt.formatted_chat_prompt)
        return True
