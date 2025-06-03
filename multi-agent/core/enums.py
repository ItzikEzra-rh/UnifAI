from enum import Enum


class ResourceCategory(str, Enum):
    LLM = "llms"
    TOOL = "tools"
    RETRIEVER = "retrievers"
    CONDITION = "conditions"
    PROVIDER = "providers"
    NODE = "nodes"
