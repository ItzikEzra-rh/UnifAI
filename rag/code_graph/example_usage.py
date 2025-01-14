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
    extractor = CodeContextExtractor(project_name="TAG_Files", repo_path="/home/cloud-user/Playground/TAG_Files", languages=["python", "go"], project_repo_path="https://github.com/kubevirt/kubevirt")
    extractor.parse_repository()
    extractor.upload_to_db()
    
    # Simulate keyword search results
    top_k_functions = [
        ("getExpectedPodName", "vm_test.go"),
        ("waitForResourceDeletion", "vm_test.go"),
        ("[test_id:3161]should carry vm.template.spec.annotations to VMI and ignore vm ones", "vm_test.go"),
        ("dump_documents", "db.py")
    ]
    
    # Get context
    # extractor = CodeContextExtractor(project_name="TAG_Files")
    context = extractor.get_context_for_functions(top_k_functions)
    
    # Format for LLM
    llm_context = format_context_for_llm(context)

    # Debug prints
    sep = f"\n{'-'*100}\n"
    print(sep)
    print(llm_context, end=sep)