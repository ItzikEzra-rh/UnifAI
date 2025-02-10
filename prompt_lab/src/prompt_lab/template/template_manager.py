import copy
import string
from jinja2 import Environment
from prompt_lab.utils.util import load_json_config
from prompt_lab.config import ConfigManager
from prompt_lab.utils.util import get_root_dir
import os


class TemplateManager:
    """
    Manages templates and their conditions, ensuring correct data retrieval and filtering.
    """

    def __init__(self):
        self.config = ConfigManager()
        self.project_config = load_json_config(self.get_template_path)
        self.__init_template_params()
        self.substitute_top_level_params()
        self.env = Environment()

    def __init_template_params(self):
        project_context = self.config.get("templates_project_context", "")
        project_id = self.config.get("project_id", "")
        project_repo = self.config.get("project_repo", "")
        if project_context:
            self.project_config["context"] = f"""{project_context}, {self.project_config["context"]}"""
        if project_id:
            self.project_config["project_id"] = project_id
        if project_repo:
            self.project_config["project_repo"] = project_repo

    def substitute_top_level_params(self):
        """Recursively substitutes string values in self.project_config using top-level parameters."""
        top_level_params = self.get_template_top_level_params()

        def substitute(item):
            if isinstance(item, str):
                return string.Template(item).safe_substitute(**top_level_params)
            elif isinstance(item, list):
                return [substitute(i) for i in item]
            elif isinstance(item, dict):
                return {k: substitute(v) for k, v in item.items()}
            return item

        self.project_config = substitute(self.project_config)

    def get_element_q_and_a(self, element_type: str):
        """Retrieve all questions grouped by categories for a given element type."""
        return [q_and_a for q_and_a in self.project_config.get("q_and_a", []) if
                element_type in q_and_a.get("element_types")]

    def is_condition_met(self, condition: str, element_data: dict) -> bool:
        """Evaluate a condition using the Jinja environment."""
        if not condition:
            return True
        return self.env.from_string(condition).render(element=element_data) == "True"

    def get_template_top_level_params(self):
        """
        Return a dict of all top-level keys whose values are scalar
        (string, number, boolean, or None), ignoring any lists or objects.
        """
        top_level_params = {
            k: copy.deepcopy(v)
            for k, v in self.project_config.items()
            if not isinstance(v, (list, dict))
        }
        return top_level_params

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

    def get_template_training_system_message(self):
        return self.project_config.get("training_system_message", "")
