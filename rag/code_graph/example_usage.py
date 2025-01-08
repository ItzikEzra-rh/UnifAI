# Example usage
from typing import Dict
import networkx as nx
from code_graph.code_context_extractor import CodeContextExtractor
from code_graph.language_parsers.language_parser import FunctionContext

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
                f"{'Package: ' + func.package_name + chr(10) if func.package_name else ''}"
                f"Signature: {func.signature}\n"
                f"Calls: {', '.join(func.calls)}\n"
                f"Called by: {', '.join(func.called_by)}\n"
                f"Source:\n{func.source_code}\n"
            )
    
    return "\n".join(sections)

if __name__ == "__main__":
    # Initialize with both Python and Go support
    extractor = CodeContextExtractor("/home/cloud-user/Projects/AI-TC-s-Generator/data-pre/code_graph/playground", languages=["python", "go"])
    extractor.parse_repository()
    
    # Simulate keyword search results
    top_k_functions = [
        ("getExpectedPodName", "/home/cloud-user/Projects/AI-TC-s-Generator/data-pre/code_graph/playground/vm_test.go"),
        ("waitForResourceDeletion", "/home/cloud-user/Projects/AI-TC-s-Generator/data-pre/code_graph/playground/vm_test.go"),
        ("dump_documents", "/home/cloud-user/Projects/AI-TC-s-Generator/data-pre/code_graph/playground/db.py")
    ]
    
    # Get context
    context = extractor.get_context_for_functions(top_k_functions)
    
    # Format for LLM
    llm_context = format_context_for_llm(context)

    # Debug prints
    sep = f"\n{'-'*100}\n"
    print(sep)
    print(llm_context, end=sep)