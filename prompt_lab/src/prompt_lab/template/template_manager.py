from jinja2 import Environment
from prompt_lab.utils.util import load_json_config
from prompt_lab.config import ConfigManager
from prompt_lab.utils.util import get_root_dir
import os


class TemplateManager:
    """
    Manages templates and their conditions, ensuring correct data retrieval and filtering.
    """
    PARAMS = ["project_id", "project_repo", "coding_language"]

    def __init__(self):
        self.project_config = load_json_config(self.get_template_path)
        self.element_templates = self.project_config.get("element_templates", {})
        self.template_used_params = self._initialize_template_params()
        self.env = Environment()

    def _initialize_template_params(self):
        """Initialize and return template parameters from the project configuration."""
        params = {}
        for param in self.PARAMS:
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

    @property
    def get_template_path(self):
        config = ConfigManager()
        return (
            os.path.join(
                str(get_root_dir()),
                config.get("templates_dir_path"),
                config.get("templates_agent"),
                f"{config.get('templates_type')}.json"
            )
            if not config.get("templates_path")
            else config.get("templates_path")
        )

    def get_template_system_message(self):
        return self.project_config.get("system_message", "")

    def get_template_context_message(self):
        return self.project_config.get("context_template", "")
