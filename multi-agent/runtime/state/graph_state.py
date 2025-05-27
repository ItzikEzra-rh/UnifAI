from typing import List, Annotated, TypedDict
from langchain_core.messages import AnyMessage
from pydantic import BaseModel, Field, ConfigDict
from typing import Any, Dict, Optional
from operator import add


class GraphState(TypedDict):
    """
    Concrete GraphState: add your
    domain-specific slots here.
    """
    # user_prompt: Annotated[str, lambda x, y: y]
    # output: Annotated[str, lambda x, y: y]
    # condition: Annotated[int, lambda x, y: y]
    user_prompt: str
    output: str
    # condition: int
