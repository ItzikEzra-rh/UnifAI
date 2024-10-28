import random


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
            element_data (dict): Dictionary containing information about the element for
                                 which prompts are generated. It includes `element_type`
                                 and other attributes required by the templates.

        Returns:
            list: A list of dictionaries, each containing a formatted prompt and metadata.
                  Each dictionary contains:
                  - `formatted_prompt` (str): The fully formatted prompt text.
                  - `metadata` (dict): Metadata associated with the prompt, including:
                      - `element_type` (str): The type of the element.
                      - `group` (str): The group name for the prompt.
                      - `category` (str): The category of the prompt.
                      - `input_text` (str): The input text generated from templates.
                      - `original_data` (dict): The original element data.
                      - `token_count` (int): The token count of the formatted prompt.

        Notes:
            - Prompts that exceed the token limit are skipped.
        """
        all_prompts = []
        element_type = element_data.get("element_type")
        input_option_groups = self.project_config["element_templates"].get(element_type, {})
        system_message = self.project_config.get("system_message", "")

        for group_name, options in input_option_groups.items():
            for category, templates in options.items():
                # Generate context and input text for the prompt
                context, input_text = self._generate_random_input(templates, **element_data)
                formatted_prompt = self._format_prompt(system_message, context, input_text)

                # Append prompt with metadata
                all_prompts.append({
                    "formatted_prompt": formatted_prompt,
                    "metadata": {
                        "element_type": element_type,
                        "group": group_name,
                        "category": category,
                        "input_text": input_text,
                        "original_data": element_data,
                    }
                })
        return all_prompts

    def _generate_random_input(self, templates, **kwargs):
        """
        Generates randomized input text from the provided templates and element data.

        Args:
            templates (list): A list of template strings for generating input text.
            **kwargs: Additional keyword arguments used for formatting the templates.

        Returns:
            tuple: A tuple containing:
                - `context` (str): The context text generated from the `context_template`
                                   in the project configuration.
                - `input_text` (str): The input text generated from a randomly selected template.
        """
        context_template = self.project_config.get("context_template", "")
        context = context_template.format(**kwargs)
        selected_template = random.choice(templates)
        input_text = selected_template.format(**kwargs)
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
