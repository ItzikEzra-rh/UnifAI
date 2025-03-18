import sys
import json
import re
from bson import json_util
from typing import Dict, List, Set
from collections import defaultdict

from rag.meta_data.helpers.meta_data_project_expander import MetaDataProjectExpander
from rag.meta_data.helpers.meta_data_retriever import MetaDataRetriever
from rag.meta_data.helpers.meta_data_query_expander import MetaDataQueryExpander
from rag.code_graph.code_context_extractor import CodeContextExtractor
from rag.code_graph.language_parsers.language_parser import FunctionContext
from rag.be_utils.db.db import mongo, Collections

from prompt_lab.utils.tokenizer import TokenizerUtils

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

def format_packages_context_for_llm(context: List[Dict], tokenizer_path: str, context_length: int) -> str:
    """Format and limit the context for LLM input while maintaining package ratio."""
    # Initialize tokenizer
    tokenizer = TokenizerUtils(tokenizer_path)
    token_limit = int(0.25 * context_length)   # Allowed token limit
    
    if not context:
        return "No relevant code context found for the given packages."
    
    # Step 1: Group signatures by package and file path
    grouped_context = defaultdict(lambda: defaultdict(list))
    for entry in context:
        grouped_context[entry["package_name"]][entry["file_path"]].append(entry["signature"])
    
    # Step 2: Compute initial token count per package
    package_token_counts = {}
    formatted_entries = {}
    
    for package, files in grouped_context.items():
        formatted_entries[package] = []
        package_text = f"Package Name: {package}\n\n"
        total_tokens = tokenizer.count_tokens(package_text)
        
        for file_path, signatures in files.items():
            file_text = f"Loc: {file_path}\n"
            file_tokens = tokenizer.count_tokens(file_text)
            signature_tokens = sum(tokenizer.count_tokens(f"Sig: {sig}\n") for sig in signatures)
            
            formatted_entries[package].append((file_text, signatures, file_tokens, signature_tokens))
            total_tokens += file_tokens + signature_tokens
        
        package_token_counts[package] = total_tokens
    
    # Step 3: Compute ratio and adjust if needed
    total_tokens_used = sum(package_token_counts.values())
    if total_tokens_used > token_limit:
        reduction_factor = token_limit / total_tokens_used
        for package in package_token_counts:
            package_token_counts[package] = int(package_token_counts[package] * reduction_factor)
    
    # Step 4: Trim signatures while maintaining ratio
    final_output = "Here is a collection of files from relevant packages to improve accuracy:\n\n"
    final_output = (
        "Here is a collection of files from relevant packages that you can use to improve your understanding and answer user queries accurately.\n"
        "Loc = Location, Sig = Signature\n\n"
    )

    for package, package_limit in package_token_counts.items():
        package_content = f"Package Name: {package}\n\n"
        remaining_tokens = package_limit
        package_has_content = False

        for file_text, signatures, file_tokens, signature_tokens in formatted_entries[package]:
            file_content = ""
            file_remaining_tokens = remaining_tokens - file_tokens
            sig_added = False

            for sig in signatures:
                sig_text = f"Sig: {sig}\n"
                sig_token_count = tokenizer.count_tokens(sig_text)

                if file_remaining_tokens >= sig_token_count:
                    file_content += sig_text
                    file_remaining_tokens -= sig_token_count
                    sig_added = True
                else:
                    break  # Stop when the limit is reached

            if sig_added:  # Add file_text only if at least one signature was added
                package_content += file_text + file_content + "\n"
                remaining_tokens = file_remaining_tokens
                package_has_content = True

        if package_has_content:
            final_output += package_content + "-----------------------------------------------------------------------------------------\n"
    
    return final_output.strip()

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

@mongo
def get_available_package_names_list_by_project(project_name: str, model_id: str) -> Set[str]:
    """Retrieve a set of unique package names for a given project."""
    
    query = {"project_name": project_name}
    projection = {"package_name": 1, "_id": 0}
    
    results = Collections.by_name('code_graph').find(query, projection)
    
    # Extract unique package names
    package_names = {doc["package_name"] for doc in results if "package_name" in doc}
    
    return package_names

def get_context_by_packages(packages_list, project_name, model_id, tokenizer_path, context_length):
    extractor = CodeContextExtractor(project_name=project_name)
    
    # Get context
    context = extractor.get_context_from_package_list(project_name, packages_list)
    
    # Format for LLM
    llm_context = format_packages_context_for_llm(context, tokenizer_path, context_length)
    return llm_context

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