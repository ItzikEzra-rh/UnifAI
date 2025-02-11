import hashlib
import copy
import string
from .prompt import Prompt
from prompt_lab.utils import logger


class PromptFormatter:
    """
    Responsible for formatting prompts, including token counting and metadata generation.
    Utilizes TemplateManager for template-related tasks.
    """

    def __init__(self, template_manager):
        self.template_manager = template_manager

    def render_context(self, element_data: dict, context: str) -> str:
        """Render the context template using the provided element data."""
        element_data = copy.deepcopy(element_data)  # Avoid modifying original data

        for key in element_data:
            value = element_data[key]
            if isinstance(value, str) and value.startswith(f"{key}:"):
                continue  # Skip if already formatted

            element_data[key] = f"{key}:\n{value}" if value else ""

        # Use safe_substitute() directly
        return string.Template(context).safe_substitute(element_data)

    def substitute_q_and_a(self, q_and_a, element_data):
        def substitute(item):
            if isinstance(item, str):
                return string.Template(item).safe_substitute(**element_data)
            elif isinstance(item, list):
                return [substitute(i) for i in item]
            elif isinstance(item, dict):
                return {k: substitute(v) for k, v in item.items()}
            return item

        return substitute(q_and_a)

    def format_prompt(self, element_data: dict, q_and_a: dict) -> Prompt:
        """Prepare a fully formatted Prompt object."""
        context = self.render_context(element_data, q_and_a.get("context"))
        q_and_a = self.substitute_q_and_a(q_and_a=q_and_a, element_data=element_data)
        name = q_and_a.get("name")
        element_type = q_and_a.get("element_type")
        seed_system_message = q_and_a.get("seed_system_message")
        question_system_message = q_and_a.get("question_system_message")
        question_seed = q_and_a.get("question_seed")
        question = q_and_a.get("question")
        answer = q_and_a.get("answer")
        question_validation = q_and_a.get("question_validation")
        answer_validation = q_and_a.get("answer_validation")
        base_id = element_data.get("uuid", "") + name
        prompt_uuid = hashlib.md5(base_id.encode()).hexdigest()
        logger.debug(f"generated prompt with UUID {prompt_uuid}")

        return Prompt(
            uuid=prompt_uuid,
            name=name,
            element_type=element_type,
            context=context,
            seed_system_message=seed_system_message,
            question_system_message=question_system_message,
            question_seed=question_seed,
            question_options=question,
            answer=answer,
            question_validation=question_validation,
            answer_validation=answer_validation,
            original_data=copy.deepcopy(element_data)
        )
