import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from noun_analyzer import NounAnalyzer, NounAnalysisConfig
import spacy
import json
from typing import List

def load_json(file_path: str) -> dict:
    """Load JSON data from a file."""
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)

def extract_questions(data: List[dict]) -> List[str]:
    """Extract all question strings from a list of objects."""
    return [item["question"] for item in data if "question" in item]

# Initialize the analyzer
analyzer = NounAnalyzer()

# data = load_json("{FILE_LOCATION}.json")
# prompts = extract_questions(data)

# Example prompts
prompts = [
    "Test the deployment of the database configuration",
    "Verify that the pod replicas are functioning correctly",
    "Check the authentication system's response time"
    # "Kubernetes pod configuration"
]

# Basic usage
noun_frequencies = analyzer.extract_nouns(prompts)

# Advanced analysis with custom configuration
config = NounAnalysisConfig(
    min_word_length=3,
    include_proper_nouns=True,
    include_compound_nouns=False
)
detailed_analysis = analyzer.analyze_noun_frequencies(prompts, config)

single_nouns_sorted = dict(sorted(detailed_analysis["single_nouns"].items(), key=lambda item: item[1], reverse=True)[:100])
print(single_nouns_sorted.keys())


# Test code to examine how spaCy processes terms

print("\n-----------------------------------------------------------")

nlp = spacy.load("en_core_web_sm")
text = "The Kubernetes pod configuration needs to be updated. MongoDB database is running."
doc = nlp(text)

# Show POS tags
print("Part of Speech Analysis:")
for token in doc:
    print(f"Word: {token.text:15} POS: {token.pos_:6} {'(Proper Noun)' if token.pos_ == 'PROPN' else '(Common Noun)' if token.pos_ == 'NOUN' else ''}")

print("\nNoun Chunks (Compound Nouns):")
for chunk in doc.noun_chunks:
    print(f"Chunk: {chunk.text}")
    print("Breakdown:")
    for token in chunk:
        print(f"  - {token.text:15} {token.pos_:6} {token.dep_:10}")