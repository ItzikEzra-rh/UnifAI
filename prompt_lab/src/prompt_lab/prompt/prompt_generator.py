from template import TemplateManager
from .prompt_formatter import PromptFormatter
from tqdm import tqdm
import random


class PromptGenerator:
    """
    Orchestrates the generation of prompts by combining TemplateManager and PromptFormatter.
    """

    def __init__(self, repository, tokenizer, project_config):
        self.repository = repository
        self.template_manager = TemplateManager(project_config)
        self.prompt_formatter = PromptFormatter(project_config, tokenizer)

    def __iter__(self):
        """Iterate over generated Prompt objects."""
        for element_data in tqdm(self.repository.input_load_data(),
                                 total=self.repository.get_input_size(),
                                 desc="Processing elements"):
            for prompt in self._generate_prompts(element_data):
                yield prompt

    def create_prompts(self, element_data):
        """Generate and return a list of Prompt objects for a given element."""
        return list(self._generate_prompts(element_data))

    def _generate_prompts(self, element_data):
        """Core logic for generating prompts from element data."""
        element_type = element_data.get("element_type")
        if not element_type:
            return

        templates = self.template_manager.get_questions(element_type)

        for group_name, categories in templates.items():
            for category_name, template_config in categories.items():
                if not self.template_manager.is_condition_met(template_config.get("condition"), element_data):
                    continue

                questions = template_config.get("questions", [])
                if not questions:
                    continue

                question_def = random.choice(questions)
                yield self.prompt_formatter.format_prompt(
                    element_data,
                    group_name,
                    category_name,
                    question_def
                )
