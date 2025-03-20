from abc import ABC, abstractmethod
from typing import List, Type, Dict

class MetaDataExtractorBase(ABC):
    # Initialize the class variable properly
    _extractors: Dict[str, Type['MetaDataExtractorBase']] = dict()

    def __init__(self, project_name: str):
        self.project_name = project_name
        
    @abstractmethod
    def extract_actions(self, text: str) -> List[str]:
        """Extract meaningful actions (verbs) from the given text."""
        pass
    
    @abstractmethod
    def extract_buzz_words(self, text: str) -> List[str]:
        """Extract resources from the given text."""
        pass

    @classmethod
    def register_extractor(cls, project_name: str, extractor_class: Type['MetaDataExtractorBase']):
        """Register a new extractor class for a specific project."""
        cls._extractors[project_name.lower()] = extractor_class
    
    @classmethod
    def create_extractor(cls, project_name: str) -> 'MetaDataExtractorBase':
        """Factory method to create the appropriate MetaDataExtractor instance."""
        extractor_class = cls._extractors.get(project_name.lower())
        if not extractor_class:
            raise ValueError(f"No metadata extractor found for project: {project_name}")
            
        return extractor_class(project_name)