from .metadata_extractor.meta_data_extractor import MetaDataExtractorBase
from .metadata_extractor.kubevirt_meta_data_extractor import KubevirtMetaDataExtractor
from .metadata_extractor.eco_go_meta_data_extractor import EcogoMetaDataExtractor
from .metadata_extractor.oadp_meta_data_extractor import OadpMetaDataExtractor

class MetaDataQueryExpander:
    def __init__(self, query, project_name, model_name, model_id):
        self.query = query
        self.project_name = project_name
        self.model_name = model_name
        self.model_id = model_id
        self.context_length = len(query)
        
        # Registeration of different extractors expected to be handled from __init__ file of the MetaDataExtractor class
        MetaDataExtractorBase.register_extractor("kubevirt", KubevirtMetaDataExtractor)
        MetaDataExtractorBase.register_extractor("eco-gotests", EcogoMetaDataExtractor)
        MetaDataExtractorBase.register_extractor("oadp", OadpMetaDataExtractor)

    def extract_metadata(self):
        """
        Generate metadata for the query.
        """
        extractor = MetaDataExtractorBase.create_extractor(self.project_name)
        actions = extractor.extract_actions(self.query)
        buzz_words = extractor.extract_buzz_words(self.query)

        metadata = {
            "type": "QUERY",
            "project_name": self.project_name,
            "action": actions,
            "buzz_words": buzz_words,
        }
    
        if self.project_name == "kubevirt":
            metadata["k8s_terms"] = extractor.extract_k8s_terms(self.query)
        
        return metadata