from rag.be_utils.db.db import mongo, Collections, db
from rag.meta_data.helpers.match_strategy.matching_strategy import MatchingContext
from rag.meta_data.helpers.match_strategy.full_mesh_strategy import FullMeshStrategy
from rag.meta_data.helpers.match_strategy.single_match__strategy import SingleMatchStrategy

class MetaDataRetriever:
    @mongo
    def __init__(self, query_metadata, project_name):
        self.query_metadata = query_metadata
        self.project_name = project_name
        self.collection = Collections.by_name('parsed_objects')

    def _kubevirt_matches(self, metadata: dict, single_matcher: MatchingContext, k8s_terms: list) -> bool:
        """Check if kubevirt-specific terms should be considered for filtering."""
        return self.project_name == "kubevirt" and single_matcher.check_match(k8s_terms, metadata.get("k8s_terms", []))

    def best_match(self):
        """
        Finds the best match objects from the DB collection 'parsed_objects'
        based on the query metadata.

        Returns:
            List of matching objects.
        """
        project_name = self.query_metadata.get('project_name')
        actions = self.query_metadata.get('action', [])
        buzz_words = self.query_metadata.get('buzz_words', [])

        # Unique key mapping for the project 'kubevirt'
        k8s_terms = self.query_metadata.get('k8s_terms', [])

        if not project_name or not (actions or buzz_words or k8s_terms):
            return []
        
        # Create matching context with desired strategy
        full_matcher = MatchingContext(FullMeshStrategy())
        single_matcher = MatchingContext(SingleMatchStrategy())

        # Query 1: Find all objects matching the project name
        project_matches = list(self.collection.find({"metadata.project_name": project_name}))

        # Query 2: Filter objects that match actions, buzz_words, and k8s_terms
        best_matches = []
        for obj in project_matches:
            metadata = obj.get("metadata", {})
            
            # Check if at least one value matches for each field
            if (
                single_matcher.check_match(actions, metadata.get("action", [])) and
                full_matcher.check_match(buzz_words, metadata.get("buzz_words", [])) and
                (self.project_name != "kubevirt" or self._kubevirt_matches(metadata, single_matcher, k8s_terms))
            ):
                best_matches.append(obj)

        return best_matches