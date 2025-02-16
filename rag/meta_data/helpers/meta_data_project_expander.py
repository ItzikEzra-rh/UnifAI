from collections import defaultdict
from rag.be_utils.db.db import mongo, Collections, db
from rag.be_utils.utils import time_execution
from .metadata_extractor.meta_data_extractor import MetaDataExtractorBase
from .metadata_extractor.kubevirt_meta_data_extractor import KubevirtMetaDataExtractor
from .metadata_extractor.eco_go_meta_data_extractor import EcogoMetaDataExtractor

class MetaDataProjectExpander:
    def __init__(self, parsed_elements, project_name, project_repo_path, naming_mapping = {}, built_in_keys = [], exclude_types = [], project_programming_languages = []):
        self.parsed_elements = parsed_elements
        self.project_name = project_name
        self.project_repo_path = project_repo_path
        self.naming_mapping = naming_mapping 
        self.built_in_keys = built_in_keys
        self.exclude_types = exclude_types 
        self.project_programming_languages = project_programming_languages
        self.required_parsed_elements = list(filter(lambda ele: not ele["element_type"] in self.exclude_types, self.parsed_elements))

        # Registeration of different extractors expected to be handled from __init__ file of the MetaDataExtractor class
        MetaDataExtractorBase.register_extractor("kubevirt", KubevirtMetaDataExtractor)
        MetaDataExtractorBase.register_extractor("eco-gotests", EcogoMetaDataExtractor)

    @time_execution
    def add_metadata(self):
        """
        Add metadata to each object in the parsed objects list.
        """
        for element in self.required_parsed_elements:
            metadata = defaultdict(list)

            for key in self.built_in_keys: 
                metadata[self.naming_mapping[key]] = element.get(key, "")

            element_name = element.get("name", "")
            element_code = element.get("code", "")
            # element_name = element.get("additional_data", {}).get("name", "") + element.get("additional_data", {}).get("documentation", "") 

            extractor = MetaDataExtractorBase.create_extractor(self.project_name)
            # metadata["id"] = extractor.extract_test_id(element_name)

            combined_text = f"{element_name} {element_code}"
            metadata["action"] = extractor.extract_actions(combined_text)
            metadata["buzz_words"] = extractor.extract_buzz_words(element_code)

            if self.project_name == "kubevirt":
                metadata["k8s_terms"] = extractor.extract_k8s_terms(combined_text)

            element["metadata"] = dict(metadata)

    @mongo
    def add_to_db(self):
        """
        Placeholder for adding parsed objects to the database.
        """
        result = Collections.by_name('parsed_objects').insert_many(self.required_parsed_elements)