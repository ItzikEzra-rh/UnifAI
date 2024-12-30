from collections import defaultdict
from .meta_data_extractor import MetaDataExtractor
from be_utils.db.db import mongo, Collections, db

class MetaDataProjectExpander:
    def __init__(self, parsed_elements, project_name, project_repo_path, project_programming_languages = []):
        self.parsed_elements = parsed_elements
        self.project_name = project_name
        self.project_repo_path = project_repo_path
        self.project_programming_languages = project_programming_languages

    def add_metadata(self):
        """
        Add metadata to each object in the parsed objects list.
        """
        for element in self.parsed_elements:
            element_name = element.get("name", "")
            element_code = element.get("code", "")
            metadata = defaultdict(list)

            metadata["project_name"] = self.project_name
            metadata["type"] = element.get("element_type", "")
            metadata["id"] = MetaDataExtractor.extract_test_id(element_name)
            metadata["location"] = element.get("file_location", "")

            combined_text = element_name + " " + element_code
            metadata["action"] = MetaDataExtractor.extract_actions(combined_text)
            metadata["k8s_terms"] = MetaDataExtractor.extract_k8s_terms(combined_text)
            metadata["resources"] = MetaDataExtractor.extract_resources(element_code)

            element["metadata"] = dict(metadata)

    @mongo
    def add_to_db(self):
        """
        Placeholder for adding parsed objects to the database.
        """
        result = Collections.by_name('parsed_objects').insert_many(self.parsed_elements)