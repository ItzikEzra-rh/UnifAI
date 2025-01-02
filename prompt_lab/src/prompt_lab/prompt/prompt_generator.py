from template import TemplateManager
from .prompt_formatter import PromptFormatter
from tqdm import tqdm


class PromptGenerator:
    """
    Orchestrates the generation of prompts by combining TemplateManager and PromptFormatter.
    """

    def __init__(self, repository, tokenizer):
        self.repository = repository
        self.template_manager = TemplateManager()
        self.prompt_formatter = PromptFormatter(self.template_manager, tokenizer)

    def __iter__(self):
        """Iterate over generated Prompt objects."""
        num_of_elements = self.repository.get_input_size()

        for element_data in tqdm(self.repository.load_input_data(),
                                 total=num_of_elements,
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

                yield self.prompt_formatter.format_prompt(
                    element_data,
                    group_name,
                    category_name,
                    questions
                )
