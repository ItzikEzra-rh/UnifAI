import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from noun_analyzer import NounAnalyzer, NounAnalysisConfig
import spacy
import json
from typing import List

def load_ndjson(file_path: str) -> list[dict]:
    """Load NDJSON data from a file."""
    with open(file_path, "r", encoding="utf-8") as file:
        return [json.loads(line) for line in file if line.strip()]

def load_json(file_path: str) -> dict:
    """Load JSON data from a file."""
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)

def extract_questions(data: List[dict]) -> List[str]:
    """Extract all question strings from a list of objects."""
    return [item["question"] for item in data if "question" in item]

# Initialize the analyzer
analyzer = NounAnalyzer()

# FILE_LOCATION representting "DPR/Prompt_Lab final JSON/NDJSON" file, which holds a list of objects in the following strcuture:
# [
#     {
#         "answer": str
#         "question": str
#     },
# ]

data = load_ndjson("{FILE_LOCATION}.ndjson")
data = load_json("{FILE_LOCATION}.json")
prompts = extract_questions(data)

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