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

    def __init__(self):
        pass

    def render_context(self, element_data: dict, context: str) -> str:
        """Render the context template using the provided element data."""
        element_data = copy.deepcopy(element_data)
        placeholders = [field_name for _, field_name, _, _ in string.Formatter().parse(context) if field_name]

        for placeholder in placeholders:
            if element_data.get(placeholder):
                value = element_data[placeholder]
                if isinstance(value, str) and value.startswith(f"{placeholder}:"):
                    continue
                element_data[placeholder] = f"{placeholder}:\n{value}" if placeholder not in element_data else ""
            else:
                element_data[placeholder] = ""

        return context.format(**element_data)

    def format_prompt(self, element_data: dict, q_and_a: dict) -> Prompt:
        """Prepare a fully formatted Prompt object."""
        context = q_and_a.get("context")
        name = q_and_a.get("name")
        element_type = q_and_a.get("element_type")
        seed_system_message = q_and_a.get("seed_system_message")
        question_system_message = q_and_a.get("question_system_message")
        question_seed = q_and_a.get("question_seed")
        question = q_and_a.get("question")
        answer = q_and_a.get("answer")
        question_validation = q_and_a.get("question_validation")
        response_validation = q_and_a.get("response_validation")
        formatted_context = self.render_context(element_data, context)
        base_id = element_data.get("uuid", "") + name
        prompt_uuid = hashlib.md5(base_id.encode()).hexdigest()
        logger.debug(f"generated prompt with UUID {prompt_uuid}")
        return Prompt(
            uuid=prompt_uuid,
            name=name,
            element_type=element_type,
            context=formatted_context,
            seed_system_message=seed_system_message,
            question_system_message=question_system_message,
            question_seed=question_seed,
            question_options=question,
            answer=answer,
            question_validation=question_validation,
            response_validation=response_validation,
            original_data=copy.deepcopy(element_data)
        )
