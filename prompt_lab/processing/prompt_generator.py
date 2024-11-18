from jinja2 import Environment
import random
import string


class PromptGenerator:
    """
    PromptGenerator is responsible for generating formatted prompts and associated metadata
    for each element based on the project configuration. It ensures that prompts adhere to
    token limits and includes relevant metadata for processing.
    """

    def __init__(self, tokenizer, project_config):
        """
        Initializes the PromptGenerator with a tokenizer and project configuration.

        Args:
            tokenizer: An instance of a tokenizer utility that provides methods for
                       formatting prompts and calculating token limits.
            project_config (dict): Dictionary containing the project configurations,
                                   including prompt templates and token limits.
        """
        self.project_config = project_config
        self.tokenizer = tokenizer

    def create_prompts(self, element_data):
        """
        Generates formatted prompts and metadata for a given element.

        Args:
            element_data (dict): Contains information about the element for
                                 which prompts are generated, including `element_type`
                                 and other attributes required by the templates.

        Returns:
            list[dict]: A list of dictionaries, each containing:
                        - `formatted_prompt` (str): The fully formatted prompt text.
                        - `metadata` (dict): Metadata associated with the prompt.
        """
        prompts = []
        element_type = element_data.get("element_type")
        input_groups = self.project_config["element_templates"].get(element_type, {})
        system_message = self.project_config.get("system_message", "")
        env = Environment()

        for group_name, categories in input_groups.items():
            for category_name, templates in categories.items():
                # Check condition if specified
                condition = templates.get("condition")
                if condition and env.from_string(condition).render(element=element_data) != "True":
                    continue

                questions = templates.get("questions", [])
                if not questions:
                    continue

                # Generate context and input text
                context, input_text = self._generate_random_input(questions, element_data)
                formatted_prompt = self._format_prompt(system_message, context, input_text)

                # Append prompt with metadata
                prompts.append({
                    "formatted_prompt": formatted_prompt,
                    "metadata": {
                        "element_type": element_type,
                        "group": group_name,
                        "category": category_name,
                        "input_text": input_text,
                        "original_data": element_data,
                    }
                })

        return prompts

    @staticmethod
    def _format_context(context_template, element):
        # Parse the template to find placeholders
        formatter = string.Formatter()
        placeholders = [field_name for _, field_name, _, _ in formatter.parse(context_template) if field_name]

        # Fill in missing keys with defaults and append "\n data" to each placeholder value
        for placeholder in placeholders:
            if not element.get(placeholder):  # Check if placeholder is missing or its value is empty
                element[placeholder] = ""
            else:
                element[placeholder] = f"{placeholder}:\n{element[placeholder]}\n"

        # Format the context
        return context_template.format(**element)

    def _generate_random_input(self, template_questions, element_data):
        """
        Generates randomized input text from the provided templates and element data.

        Args:
            template_questions (list): A list of template strings for generating input text.
            **kwargs: Additional keyword arguments used for formatting the templates.

        Returns:
            tuple: A tuple containing:
                - `context` (str): The context text generated from the `context_template`
                                   in the project configuration.
                - `input_text` (str): The input text generated from a randomly selected template.
        """
        context_template = self.project_config.get("context_template", "")
        context = self._format_context(context_template, element_data)
        selected_template = random.choice(template_questions)
        input_text = selected_template.format(**element_data)
        return context, input_text

    def _format_prompt(self, system_message, context, input_text):
        """
        Formats the final prompt by combining the system message, context, and user input.

        Args:
            system_message (str): The system message, serving as an initial context for the prompt.
            context (str): The context generated for the prompt based on the element data.
            input_text (str): The main input text of the prompt generated from templates.

        Returns:
            str: The fully formatted prompt, ready for tokenization and processing.
        """
        return self.tokenizer.format_chat_prompt([
            {"role": "system", "content": system_message},
            {"role": "context", "content": context},
            {"role": "user", "content": input_text}
        ])
