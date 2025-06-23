from typing import Generic, List, TypeVar, Union
from uuid import uuid4
from pydantic import BaseModel, Field, Extra

# -----------------------------------------------------------------------------
# Import the *catalog* specs (single source of truth for field validation)
# -----------------------------------------------------------------------------
from nodes.models.base_node import NodeSpec
from llms.models.base_llm import LLMsSpec
from retrievers.models.retriever_config import RetrieversSpec
from condition.models.base_condition import ConditionSpec
from tools.models.tool_config import ToolsSpec
from providers.models.base_provider import ProviderSpec


# ─────────────────────────────────────────────────────────────────────────────
# Author-time helper types
# ─────────────────────────────────────────────────────────────────────────────
class Ref(BaseModel):
    """Wraps a registry reference: {"$ref": "llm:abcd-1234"}"""
    ref: str = Field(..., alias="$ref")

    class Config:
        extra = Extra.forbid
        validate_by_name = True  # keep `$ref` key in JSON


T = TypeVar("T", bound=BaseModel)


class Resource(BaseModel, Generic[T]):
    """
    Catalogue entry in a *draft* blueprint.
    • alias  – blueprint-local identifier (unique per catalogue/kind)
    • name   – optional human label
    • config – either a live `$ref` or a frozen inline spec (T)
    """
    alias: str
    config: Union[Ref, T]

    class Config:
        extra = Extra.forbid


class ResourceSpec(BaseModel, Generic[T]):
    """Same shape after resolution – config is always the concrete spec."""
    alias: str
    config: T

    class Config:
        extra = Extra.forbid


# ─────────────────────────────────────────────────────────────────────────────
#  Graph plan
# ─────────────────────────────────────────────────────────────────────────────
class StepMeta(BaseModel):
    description: str = ""
    display_name: str = ""
    tags: List[str] = []

    class Config:
        extra = Extra.forbid


class StepDef(BaseModel):
    alias: str = Field(  # step id (local)
        default_factory=lambda: f"s_{uuid4().hex[:8]}"
    )
    after: str | List[str] | None = None  # depends-on
    node: str  # <-- node.alias
    exit_condition: str | None = None
    branches: dict | None = None
    meta: StepMeta = Field(default_factory=StepMeta)

    class Config:
        extra = Extra.forbid


# ─────────────────────────────────────────────────────────────────────────────
#  Top-level blueprints
# ─────────────────────────────────────────────────────────────────────────────
class BlueprintDraft(BaseModel):
    """UI-authorable document (may contain $refs)."""
    providers: List[Resource[ProviderSpec]] = []
    llms: List[Resource[LLMsSpec]] = []
    retrievers: List[Resource[RetrieversSpec]] = []
    tools: List[Resource[ToolsSpec]] = []
    nodes: List[Resource[NodeSpec]] = []
    conditions: List[Resource[ConditionSpec]] = []

    plan: List[StepDef]

    name: str = "Untitled blueprint"
    description: str = ""

    class Config:
        extra = Extra.forbid


class BlueprintSpec(BaseModel):
    """What the graph-builder composer consumes – every $ref resolved."""
    providers: List[ResourceSpec[ProviderSpec]]
    llms: List[ResourceSpec[LLMsSpec]]
    retrievers: List[ResourceSpec[RetrieversSpec]]
    tools: List[ResourceSpec[ToolsSpec]]
    nodes: List[ResourceSpec[NodeSpec]]
    conditions: List[ResourceSpec[ConditionSpec]] = []

    plan: List[StepDef]

    name: str
    description: str

    class Config:
        extra = Extra.forbid
