from typing import List, Annotated, TypedDict
# from langchain_core.messages import add_messages
from pydantic import BaseModel, Field, ConfigDict
from typing import Any, Dict, Optional
from operator import add


def append_dict_to_list(existing, new_item) -> list[dict]:
    if not isinstance(existing, list):
        existing = []

    if isinstance(new_item, list):
        out = existing
        for single in new_item:
            out = append_dict_to_list(out, single)
        return out

    if not isinstance(new_item, dict):
        return existing

    if new_item in existing:
        return existing

    return existing + [new_item]


class GraphState(TypedDict):
    """
    Concrete GraphState: add your
    domain-specific slots here.
    """
    user_prompt: Annotated[str, lambda x, y: y]
    nodes_output: Annotated[list[dict], append_dict_to_list]
    output: str
