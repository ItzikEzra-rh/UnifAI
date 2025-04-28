from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal


class NodeTemplate(BaseModel):
    """
    Defines a pre-registered node's default atomic elements.
    Used by ComponentRegistry to store reusable templates.
    """
    name: str
    type: str  # e.g. "custom_agent", "tool_node"
    llm: str  # default LLM key
    retriever: str  # default retriever key
    tools: List[str] = []  # default tool keys
    system_message: str  # default prompt or message


class NodeSpec(BaseModel):
    """
    User-specified node configuration in a plan step.
    Either reference a template by 'ref', or define atomic fields directly.
    """
    ref: Optional[str] = None
    type: Optional[Literal["custom_agent", "tool_node", "discussion", "critic"]] = None
    llm: Optional[str] = None
    retriever: Optional[str] = None
    tools: List[str] = []
    system_message: Optional[str] = None

    # For tool_node-specific usage:
    tool: Optional[str] = None
    input_map: Dict[str, str] = {}

    # For branching/loop exit:
    exit_condition: Optional[str] = None
    branches: Dict[str, str] = {}

    def validate_mode(self):
        """
        Ensure exactly one of 'ref' or 'type' is specified,
        so we know whether to pull a template or instantiate inline.
        """
        if bool(self.ref) == bool(self.type):
            raise ValueError("NodeSpec must have exactly one of 'ref' or 'type'.")
