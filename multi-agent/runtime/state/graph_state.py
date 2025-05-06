from typing import List, Annotated, TypedDict
# from langchain_core.messages import add_messages
from pydantic import BaseModel, Field, ConfigDict
from typing import Any, Dict, Optional
from operator import add


def append_dict_to_list(existing_list: list[dict], new_dict: dict) -> list[dict]:
    return existing_list + [new_dict]


class GraphState(TypedDict):
    """
    Concrete GraphState: add your
    domain-specific slots here.
    """
    # user_prompt: Annotated[str, lambda x, y: y]
    # output: Annotated[str, lambda x, y: y]
    # condition: Annotated[int, lambda x, y: y]
    user_prompt: Annotated[str, lambda x, y: y]
    agents_output: Annotated[list[dict], append_dict_to_list]
    output: str
    # condition: int
