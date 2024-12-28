from jinja2 import Environment
from config import config


class TemplateManager:
    """
    Manages templates and their conditions, ensuring correct data retrieval and filtering.
    """

    def __init__(self, project_config: dict):
        self.project_config = project_config
        self.element_templates = project_config.get("element_templates", {})
        self.template_used_params = self._initialize_template_params()
        self.env = Environment()

    def _initialize_template_params(self):
        """Initialize and return template parameters from the project configuration."""
        params = {}
        for param in config.get("templates.usable_params", []):
            val = self.project_config.get(param)
            if val:
                params[param] = val
        return params

    def get_questions(self, element_type: str):
        """Retrieve all questions grouped by categories for a given element type."""
        return self.element_templates.get(element_type, {})

    def is_condition_met(self, condition: str, element_data: dict) -> bool:
        """Evaluate a condition using the Jinja environment."""
        if not condition:
            return True
        return self.env.from_string(condition).render(element=element_data) == "True"

    def get_template_params(self):
        """Expose template parameters for external use."""
        return self.template_used_params
