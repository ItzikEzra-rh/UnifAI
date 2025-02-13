from typing import Dict, List, Set
from collections import Counter
import spacy
from logging import getLogger
from dataclasses import dataclass

logger = getLogger(__name__)

@dataclass
class NounAnalysisConfig:
    """Configuration for noun analysis settings."""
    min_word_length: int = 3
    exclude_technical_terms: bool = False
    include_proper_nouns: bool = True
    include_compound_nouns: bool = True

class NounAnalyzer:
    """
    A class for analyzing and extracting nouns from text prompts using NLP.
    
    This class provides functionality to process text and identify significant nouns,
    filtering out unwanted terms and providing frequency analysis.
    """
    
    def __init__(self, model: str = "en_core_web_sm"):
        """
        Initialize the NounAnalyzer with specified spaCy model.
        
        Args:
            model (str): Name of the spaCy model to use. Defaults to "en_core_web_sm".
        
        Raises:
            ImportError: If the specified spaCy model is not installed.
        """
        try:
            self.nlp = spacy.load(model)
        except OSError as e:
            logger.error(f"Failed to load spaCy model '{model}': {str(e)}")
            raise ImportError(f"Please install the {model} model using: python -m spacy download {model}")

    @staticmethod
    def is_significant_noun(token: spacy.tokens.Token, config: NounAnalysisConfig) -> bool:
        """
        Determine if a token represents a significant noun based on configuration.
        
        Args:
            token: spaCy token to analyze
            config: Configuration settings for noun analysis
            
        Returns:
            bool: True if the token is a significant noun, False otherwise
        """
        # Basic noun check
        is_noun = token.pos_ in ("NOUN", "PROPN") if config.include_proper_nouns else token.pos_ == "NOUN"
        
        # Apply filters
        meets_criteria = (
            is_noun
            and token.is_alpha
            and len(token.text) >= config.min_word_length
            and not token.is_stop
            and not token.is_punct
        )
        
        return meets_criteria

    def extract_nouns(self, prompts: List[str], config: NounAnalysisConfig = NounAnalysisConfig()) -> Dict[str, int]:
        """
        Extract and count nouns from a list of prompts.
        
        Args:
            prompts: List of text prompts to analyze
            config: Configuration settings for noun analysis
            
        Returns:
            Dict[str, int]: Dictionary mapping nouns to their frequency counts
            
        Raises:
            ValueError: If prompts list is empty or contains non-string elements
        """
        if not prompts:
            raise ValueError("Prompts list cannot be empty")
        
        if not all(isinstance(prompt, str) for prompt in prompts):
            raise ValueError("All prompts must be strings")

        noun_counter: Counter = Counter()
        
        for prompt in prompts:
            try:
                doc = self.nlp(prompt)
                
                # Extract nouns that meet our criteria
                nouns = [
                    token.lemma_.lower()
                    for token in doc
                    if self.is_significant_noun(token, config)
                ]
                
                # Update counter
                noun_counter.update(nouns)
                
            except Exception as e:
                logger.warning(f"Error processing prompt '{prompt[:50]}...': {str(e)}")
                continue
        
        return dict(noun_counter)

    def get_compound_nouns(self, doc: spacy.tokens.Doc) -> Set[str]:
        """
        Extract compound nouns from a spaCy Doc object.
        
        Args:
            doc: Processed spaCy Doc object
            
        Returns:
            Set[str]: Set of compound nouns found in the document
        """
        compound_nouns = set()
        
        for chunk in doc.noun_chunks:
            # Only consider chunks with multiple tokens
            if len(chunk) > 1:
                # Clean and normalize the chunk
                clean_chunk = ' '.join(
                    token.lemma_.lower()
                    for token in chunk
                    if not token.is_stop and token.is_alpha
                )
                if clean_chunk:
                    compound_nouns.add(clean_chunk)
        
        return compound_nouns

    def analyze_noun_frequencies(self, prompts: List[str], 
                               config: NounAnalysisConfig = NounAnalysisConfig()) -> Dict[str, Dict]:
        """
        Perform comprehensive noun analysis including frequencies and compound nouns.
        
        Args:
            prompts: List of text prompts to analyze
            config: Configuration settings for noun analysis
            
        Returns:
            Dict containing:
                - 'single_nouns': Dictionary of single noun frequencies
                - 'compound_nouns': Dictionary of compound noun frequencies (if enabled)
                - 'statistics': Dictionary of analysis statistics
        """
        single_nouns = self.extract_nouns(prompts, config)
        
        result = {
            'single_nouns': single_nouns,
            'statistics': {
                'total_unique_nouns': len(single_nouns),
                'total_noun_occurrences': sum(single_nouns.values()),
                'prompts_analyzed': len(prompts)
            }
        }
        
        if config.include_compound_nouns:
            compound_nouns: Counter = Counter()
            for prompt in prompts:
                doc = self.nlp(prompt)
                compound_nouns.update(self.get_compound_nouns(doc))
            
            result['compound_nouns'] = dict(compound_nouns)
            result['statistics']['unique_compound_nouns'] = len(compound_nouns)
        
        return result
    
"""
Nouns vs Compound Nouns in NLP:
    Single Nouns: 
        These are individual words that function as nouns in a sentence. In spaCy, they are identified by their Part-of-Speech (POS) tags as either "NOUN" or "PROPN" (proper noun). Examples: "database", "system", "configuration"
    
    Compound Nouns:
        These are groups of two or more words that function together as a single noun unit. In spaCy, they are identified through "noun chunks" - phrases that combine to create a single noun meaning. Examples: "database configuration", "pod replica", "authentication system"

PROPN vs NOUN in spaCy:
    NOUN (Common Noun):
        Represents general names for objects, ideas, concepts
        Examples: "computer", "database", "configuration", "deployment"
        Not capitalized (unless at start of sentence)
        Refers to a class of entities rather than specific instances

    PROPN (Proper Noun):
        Represents specific names of unique entities
        Examples: "Kubernetes", "Docker", "Jenkins", "Linux"
        Usually capitalized
        Refers to specific, individual entities
"""