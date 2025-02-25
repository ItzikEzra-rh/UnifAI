from prompt_lab.template import TemplateManager
from .prompt_formatter import PromptFormatter
from prompt_lab.utils import logger
import copy
import string


class PromptGenerator:
    """
    Orchestrates the generation of prompts by combining TemplateManager and PromptFormatter.
    """

    def __init__(self, repository):
        self.repository = repository
        self.template_manager = TemplateManager()
        self.prompt_formatter = PromptFormatter(self.template_manager)

    def __iter__(self):
        """Iterate over generated Prompt objects."""
        for element_data in self.repository.load_input_data():
            for prompt in self._generate_prompts(element_data):
                yield prompt

    def set_number_of_elements_and_prompts(self):
        logger.info("getting prompts and elements count...")
        elements_count = self.repository.get_elements_size()
        prompts_count = self.repository.get_prompts_size()

        if not elements_count and not prompts_count:
            logger.info("[PromptGenerator] prompts and elements count are not initialized, reading repo to init.")
            for element_data in self.repository.load_input_data():
                for _ in self._generate_prompts(element_data):
                    prompts_count += 1
                elements_count += 1
            self.repository.set_elements_size(elements_count)
            self.repository.set_prompts_size(prompts_count)

        logger.info(f"elements count: {elements_count}.")
        logger.info(f"prompts count: {prompts_count}.")

    def create_prompts(self, element_data):
        """Generate and return a list of Prompt objects for a given element."""
        return list(self._generate_prompts(element_data))

    def _generate_prompts(self, element_data):
        """Core logic for generating prompts from element data."""
        element_type = element_data.get("element_type")
        if not element_type:
            return

        element_q_and_a = copy.deepcopy(self.template_manager.get_element_q_and_a(element_type=element_type))

        for q_and_a in element_q_and_a:
            if not self.template_manager.is_condition_met(q_and_a.get("condition"), element_data):
                continue

            yield self.prompt_formatter.format_prompt(
                element_data,
                q_and_a)
