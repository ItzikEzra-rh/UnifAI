from typing import Any, Dict, List
class PromptFormatter:
    """Handles the formatting of prompts for the LLM."""
    
    @staticmethod
    def format_chat_prompt(system_message: str, context: str) -> List[Dict[str, str]]:
        """Format the prompt in chat-style for the LLM."""
        return [
            {"role": "system", "content": system_message},
            {"role": "user", "content": context}
        ]

    @staticmethod
    def create_prompt(element: Dict[str, Any]) -> List[Dict[str, str]]:
        """Create a prompt based on the input and output of the element."""
        system_message = (
            "You are a reviewer. Rate the output based on the following criteria, using a scale from 1 to 10. "
            "Respond with only a single number from 1 to 10, with no additional text or punctuation.\n\n"
            "Relevance: Assess how well the output addresses the input request. A high score reflects a strong, "
            "meaningful connection between the input and output.\n\n"
            "Absence of Hallucinations: Ensure the output does not contain irrelevant or invented information. "
            "This includes:\n"
            "- Repetitive phrases or nonsensical strings (e.g., 'create bool create bool create bool').\n"
            "- Incomplete or trailing sentences.\n"
            "- Sections of text that do not contribute meaningfully to the requested answer.\n"
            "Any presence of hallucinated content should result in a failing score.\n\n"
            "Quality: Evaluate the clarity, coherence, and completeness of the output. A high-quality response is "
            "well-structured, concise, and directly addresses the input without errors, unnecessary repetition, or "
            "extraneous information.\n\n"
            "Based on these criteria, provide only a single number from 1 to 10, without any additional characters."
        )

        input_text = element.get("input", "No input provided.")
        output_text = element.get("output", "No output provided.")
        context = f"Input: {input_text}\nOutput: {output_text}\n\nYour score (1-10):"

        return PromptFormatter.format_chat_prompt(system_message, context)