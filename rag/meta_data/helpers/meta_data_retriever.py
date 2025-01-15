from rag.be_utils.db.db import mongo, Collections, db

class MetaDataRetriever:
    @mongo
    def __init__(self, query_metadata):
        self.query_metadata = query_metadata
        self.collection = Collections.by_name('parsed_objects')

    def best_match(self):
        """
        Finds the best match objects from the DB collection 'parsed_objects'
        based on the query metadata.

        Returns:
            List of matching objects.
        """
        project_name = self.query_metadata.get('project_name')
        actions = self.query_metadata.get('action', [])
        resources = self.query_metadata.get('resources', [])
        k8s_terms = self.query_metadata.get('k8s_terms', [])

        if not project_name or not (actions or resources or k8s_terms):
            return []

        # Query 1: Find all objects matching the project name
        project_matches = list(self.collection.find({"metadata.project_name": project_name}))

        # Query 2: Filter objects that match actions, resources, and k8s_terms
        best_matches = []
        for obj in project_matches:
            metadata = obj.get("metadata", {})
            
            # Check if at least one value matches for each field
            if (
                any(action in metadata.get("action", []) for action in actions) and
                any(resource in metadata.get("resources", []) for resource in resources) and
                any(term in metadata.get("k8s_terms", []) for term in k8s_terms)
            ):
                best_matches.append(obj)

        return best_matches