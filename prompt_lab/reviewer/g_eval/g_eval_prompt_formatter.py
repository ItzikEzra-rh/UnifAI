from reviewer.g_eval.config import EvalCriterion
from typing import Any, Dict, List

class GEvalPromptFormatter:
    """Handles the formatting of prompts for GEval-based evaluation."""

    @staticmethod
    def format_chat_prompt(criterion: EvalCriterion, 
                        element: Dict[str, Any]) -> List[Dict[str, str]]:
        """Format the prompt in chat-style for the LLM using GEval criterion."""
        # Extract data from original_data
        original_data = element.get("original_data", {})

        # Format the detailed context of the input
        input_context = (
            f"Here is detailed information about the {element['element_type']} {original_data.get('name', 'unnamed')}:\n\n"
            f"{original_data.get('file_location', 'No location provided')}\n\n"
            f"{original_data.get('package', 'No package information')}\n\n"
            f"{original_data.get('imports', 'No imports')}\n\n"
            f"{original_data.get('global_vars', 'No global variables')}\n\n"
            f"Code for {element['element_type']} {original_data.get('name', 'unnamed')}: \n"
            f"```go\n{original_data.get('code', 'No code provided')}\n```\n\n"
        )
        
        context = criterion.format_prompt(
            element_type=element.get("element_type", "unknown"),
            # name=original_data.get("name", "unnamed"),
            input_context=input_context,
            question=element.get("input", "No input provided."),
            provided_output=element.get("output", "No output provided.")
        )
        
        return [
            {"role": "system", "content": (
                "You are an expert evaluator. Analyze how accurately the 'Provided Output'"
                "answers the 'Question', taking into account all the 'Context' provided. "
                "Provide a numerical score only."
            )},
            {"role": "user", "content": context}
        ]