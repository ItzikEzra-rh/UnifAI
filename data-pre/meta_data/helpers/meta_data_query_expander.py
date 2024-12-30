from .meta_data_extractor import MetaDataExtractor
class MetaDataQueryExpander:
    def __init__(self, query, model_name, model_id):
        self.query = query
        self.model_name = model_name
        self.model_id = model_id
        self.context_length = len(query)

    def extract_metadata(self):
        """
        Generate metadata for the query.
        """
        actions = MetaDataExtractor.extract_actions(self.query)
        resources = MetaDataExtractor.extract_resources(self.query)
        k8s_terms = MetaDataExtractor.extract_k8s_terms(self.query)

        return {
            "type": "QUERY",
            "action": actions,
            "resources": resources,
            "k8s_terms": k8s_terms
        }