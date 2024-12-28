# my_project/processing/prompt_generator.py

import hashlib
import random
import string
import copy

from models.prompt import Prompt
from template.template_manager import TemplateManager

class PromptGenerator:
    """
    An iterator that:
      - Reads data from a repository
      - For each element, uses TemplateManager to produce one or more Prompt objects
      - Yields them
    """

    def __init__(self, repository, tokenizer, project_config):
        """
        Args:
            repository: DataRepository that provides .load_data() iter of dict
            tokenizer: has tokenize() or count_tokens() method
            project_config: includes system_message, templates, etc.
        """
        self.repository = repository
        self.tokenizer = tokenizer
        self.template_manager = TemplateManager(project_config)
        self.project_config = project_config

        # Precompute any additional config
        self.system_message = self.template_manager.system_message
        self.element_templates = self.template_manager.element_templates

        from config.manager import config
        template_params_list = config.get("templates.usable_params", [])
        self.template_used_params = {}
        for param in template_params_list:
            val = project_config.get(param)
            if val:
                self.template_used_params[param] = val

    def __iter__(self):
        """
        Returns an iterator over Prompt objects.
        """
        for element_data in self.repository.load_data():
            element_type = element_data.get("element_type")
            if not element_type:
                continue  # Skip if there's no element_type

            groups = self.element_templates.get(element_type, {})
            for group_name, categories in groups.items():
                for category_name, template_config in categories.items():
                    # If there's a condition, evaluate it
                    condition = template_config.get("condition")
                    if condition and self.template_manager.env.from_string(condition).render(
                            element=element_data) != "True":
                        continue

                    questions = template_config.get("questions", [])
                    if not questions:
                        continue

                    # For each question in that category
                    for q in questions:
                        yield self._create_prompt(element_data, group_name, category_name, q)

    def _create_prompt(self, element_data, group_name, category_name, question_def):
        # 1) Render context
        context_text = self._render_context(element_data)

        # 2) Prepare user_input & validation
        user_input = question_def["question"].format(**{**element_data, **self.template_used_params})
        validation_text = question_def["validation"].format(**{**element_data, **self.template_used_params})

        # 3) Format final prompt
        formatted_prompt = self.template_manager.format_prompt(
            self.system_message,
            context_text,
            user_input
        )

        # 4) Generate stable UUID
        base_id = element_data.get("uuid", "") + group_name + category_name
        prompt_uuid = hashlib.md5(base_id.encode()).hexdigest()

        # 5) Count tokens
        token_count = self._count_tokens(formatted_prompt)

        # 6) Build metadata
        metadata = {
            "element_type": element_data.get("element_type"),
            "group": group_name,
            "category": category_name,
            "validation": validation_text,
            "input_text": user_input,
            "original_data": element_data
        }

        return Prompt(
            uuid=prompt_uuid,
            formatted_prompt=formatted_prompt,
            metadata=metadata,
            token_count=token_count
        )

    def _render_context(self, element_data: dict) -> str:
        return self.template_manager.render_context(element_data, self.template_used_params)

    def _count_tokens(self, text: str) -> int:
        """
        Use your tokenizer.
        For example:
          - tokenizer.tokenize(text) returns a list of tokens -> len(...)
          - or tokenizer.count_tokens(text)
        """
        if hasattr(self.tokenizer, "count_tokens"):
            return self.tokenizer.count_tokens(text)
        elif hasattr(self.tokenizer, "tokenize"):
            return len(self.tokenizer.tokenize(text))
        return 0
