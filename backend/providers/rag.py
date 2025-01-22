import sys
import json
import re
from bson import json_util
from typing import Dict

from rag.meta_data.helpers.meta_data_project_expander import MetaDataProjectExpander
from rag.meta_data.helpers.meta_data_retriever import MetaDataRetriever
from rag.meta_data.helpers.meta_data_query_expander import MetaDataQueryExpander
from rag.code_graph.code_context_extractor import CodeContextExtractor
from rag.code_graph.language_parsers.language_parser import FunctionContext

def format_context_for_llm(context: Dict[str, FunctionContext]) -> str:
    """Format the context in a way that's suitable for LLM input."""
    sections = []
    
    # Group functions by language
    by_language = {}
    for func in context.values():
        by_language.setdefault(func.language, []).append(func)
    
    for language, functions in by_language.items():
        sections.append(f"\n=== {language.upper()} Functions ===\n")
        
        for func in functions:
            sections.append(
                f"Function: {func.name}\n"
                f"File: {func.file_path}\n"
                f"Package: {func.package_name} {chr(10) if func.package_name else ''}"
                f"Signature: {func.signature}\n"
                # f"Calls: {', '.join(func.calls)}\n"
                # f"Called by: {', '.join(func.called_by)}\n"
                f"Source:\n{func.source_code}\n"
            )
    
    return "\n".join(sections)

def name_to_path_tuple_generator(data):
    result = []
    for item in data:
        name = item.get("name")
        location = item.get("location", "")

        # Extract location using regex
        match = re.search(r"File Location:\s*(.+)", location)
        if match:
            file_location = match.group(1).strip()
            result.append((name, file_location))

    return result

def read_file(file_path):
    """
    Reads a JSON file and returns its content as a Python object.
    """
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Failed to decode JSON from file at {file_path}")
        sys.exit(1)

def parsed_elements_metadata_expansion(parsed_elements_location, project_name, project_repo_path, naming_mapping, built_in_keys, exclude_types, project_programming_languages):
    # Path to the JSON file containing parsed objects
    parsed_elements = read_file(parsed_elements_location)

    project_meta_expander = MetaDataProjectExpander(
        parsed_elements=parsed_elements,
        project_name=project_name,
        project_repo_path=project_repo_path,
        naming_mapping=naming_mapping,
        built_in_keys=built_in_keys,
        exclude_types=exclude_types,
        project_programming_languages=project_programming_languages
    )

    # Add metadata to each parsed element & Add the entire elements to the DB
    project_meta_expander.add_metadata()
    project_meta_expander.add_to_db()

def query_meta_data_retrieval(text, project_name, model_name, model_id):
    query_meta_expander = MetaDataQueryExpander(
        query=text,
        project_name=project_name,
        model_name=model_name,
        model_id=model_id
    )

    # Extract metadata for the query
    query_metadata = query_meta_expander.extract_metadata()

    meta_data_retreiver = MetaDataRetriever(query_metadata=query_metadata)
    best_match = meta_data_retreiver.best_match()

    # Serialize the best_match list properly, including ObjectId handling
    best_match_top_relevant_keys = map(lambda ele: {'type': ele['element_type'], 'name': ele['name'], 'location': ele['file_location']} ,best_match)    
    best_match_serialized = json.loads(json_util.dumps(best_match_top_relevant_keys))
    return name_to_path_tuple_generator(best_match_serialized)

def project_graph_expansion(repo_location, project_name, project_repo_path, repo_languages):
    extractor = CodeContextExtractor(project_name=project_name, repo_path=repo_location, languages=repo_languages, project_repo_path=project_repo_path)
    
    # Retrieve graph representation to each code section & Add the entire graph elements to the DB
    extractor.parse_repository()
    extractor.upload_to_db()

def meta_data_to_graph_retrieval(project_name, relevant_metadata):
    extractor = CodeContextExtractor(project_name=project_name)
    
    # Get context
    context = extractor.get_context_for_functions(relevant_metadata)
    
    # Format for LLM
    llm_context = format_context_for_llm(context)
    return llm_context