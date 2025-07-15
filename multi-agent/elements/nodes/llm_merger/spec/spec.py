from elements.common.base_element_spec import BaseElementSpec
from core.enums import ResourceCategory
from ..config import MergerLLMNodeConfig
from ..llm_merger_node_factory import LLMMergerNodeFactory


class LLMMergerNodeElementSpec(BaseElementSpec):
    """Element specification for LLM Merger Node."""

    category = ResourceCategory.NODE
    type_key = "merger_node"
    name = "Merger Node"
    description = "Aggregates and synthesizes agent outputs"
    config_schema = MergerLLMNodeConfig
    factory_cls = LLMMergerNodeFactory
    tags = ["node", "merger", "llm", "aggregation", "synthesis"]
