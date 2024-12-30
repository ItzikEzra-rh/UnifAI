import hashlib
import copy
import string
from prompt import Prompt
from template import TemplateManager


class PromptFormatter:
    """
    Responsible for formatting prompts, including token counting and metadata generation.
    Utilizes TemplateManager for template-related tasks.
    """

    def __init__(self, template_manager: TemplateManager, tokenizer):
        self.template_manager = template_manager
        self.tokenizer = tokenizer
        self.system_message = template_manager.get_template_system_message()
        self.context_template = template_manager.get_template_context_message()

    def render_context(self, element_data: dict) -> str:
        """Render the context template using the provided element data."""
        template_params = self.template_manager.get_template_params()
        combined_data = {**copy.deepcopy(element_data), **template_params}
        placeholders = [field_name for _, field_name, _, _ in string.Formatter().parse(self.context_template) if
                        field_name]

        for placeholder in placeholders:
            if combined_data.get(placeholder):
                value = combined_data[placeholder]
                if isinstance(value, str) and value.startswith(f"{placeholder}:"):
                    continue
                combined_data[placeholder] = f"{placeholder}:\n{value}"
            else:
                combined_data[placeholder] = ""

        return self.context_template.format(**combined_data)

    def format_prompt(self, element_data: dict, group_name: str, category_name: str, question_def: dict) -> Prompt:
        """Prepare a fully formatted Prompt object."""
        context_text = self.render_context(element_data)
        template_params = self.template_manager.get_template_params()
        user_input = question_def["question"].format(**{**element_data, **template_params})
        validation_text = question_def["validation"].format(**{**element_data, **template_params})

        formatted_prompt = self.tokenizer.format_chat_prompt([
            {"role": "system", "content": self.system_message},
            {"role": "context", "content": context_text},
            {"role": "user", "content": user_input}
        ])

        base_id = element_data.get("uuid", "") + group_name + category_name
        prompt_uuid = hashlib.md5(base_id.encode()).hexdigest()

        return Prompt(
            uuid=prompt_uuid,
            formatted_prompt=formatted_prompt,
            metadata={
                "element_type": element_data.get("element_type"),
                "group": group_name,
                "category": category_name,
                "validation": validation_text,
                "input_text": user_input,
                "original_data": element_data
            },
            token_count=self._count_tokens(formatted_prompt)
        )

    def _count_tokens(self, text: str) -> int:
        """Count tokens in the provided text using the tokenizer."""
        if hasattr(self.tokenizer, "count_tokens"):
            return self.tokenizer.count_tokens(text)
        elif hasattr(self.tokenizer, "tokenize"):
            return len(self.tokenizer.tokenize(text))
        return 0
