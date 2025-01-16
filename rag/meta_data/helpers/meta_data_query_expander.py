from .metadata_extractor.meta_data_extractor import MetaDataExtractorBase
from .metadata_extractor.kubevirt_meta_data_extractor import KubevirtMetaDataExtractor
class MetaDataQueryExpander:
    def __init__(self, query, project_name, model_name, model_id):
        self.query = query
        self.project_name = project_name
        self.model_name = model_name
        self.model_id = model_id
        self.context_length = len(query)
        
        # Registeration of different extractors expected to be handled from __init__ file of the MetaDataExtractor class
        MetaDataExtractorBase.register_extractor("kubevirt", KubevirtMetaDataExtractor)

    def extract_metadata(self):
        """
        Generate metadata for the query.
        """
        extractor = MetaDataExtractorBase.create_extractor(self.project_name)
        actions = extractor.extract_actions(self.query)
        resources = extractor.extract_resources(self.query)
        k8s_terms = extractor.extract_k8s_terms(self.query)

        return {
            "type": "QUERY",
            "project_name": self.project_name,
            "action": actions,
            "resources": resources,
            "k8s_terms": k8s_terms
        }