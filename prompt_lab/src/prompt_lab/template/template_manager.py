# my_project/template/template_manager.py

import copy
import string
from jinja2 import Environment


class TemplateManager:
    """
    Handles rendering of prompts using Jinja or simple string.format
    for system/context/user messages.
    """

    def __init__(self, project_config: dict):
        self.project_config = project_config
        self.system_message = project_config.get("system_message", "")
        self.context_template = project_config.get("context_template", "")
        self.element_templates = project_config.get("element_templates", {})
        self.env = Environment()

    def render_context(self, element_data: dict, extra_params: dict = None) -> str:
        """
        Render the context_template with placeholders from element_data + extra_params.
        """
        combined = copy.deepcopy(element_data)
        if extra_params:
            combined.update(extra_params)

        return self.context_template.format(**combined)

    def format_prompt(self, system_message: str, context_text: str, user_input: str) -> str:
        """
        Combine system_message, context_text, and user_input in some standardized way.
        """
        return f"[SYSTEM]: {system_message}\n[CONTEXT]: {context_text}\n[USER]: {user_input}"
