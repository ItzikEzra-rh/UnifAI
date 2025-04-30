# graph/node_factory.py

from typing import Any, Dict
from pydantic import ValidationError

from registry import element_registry
from session.session_registry import SessionRegistry
from schemas.node_config import BaseNodeConfig
from schemas.blueprint_schema import NodeSpec
from plugins.base_factory import BaseFactory
from plugins.exceptions import PluginConfigurationError
from nodes.base_node import BaseNode


class NodeFactory:
    """
    Orchestrates creation of all BaseNode instances by:
      1) Looking up the registered factory class & config schema
      2) Validating & merging inline overrides via Pydantic
      3) Resolving session-scoped dependencies (LLM, retriever, tools)
      4) Delegating instantiation to the factory.create(...)
    """

    @staticmethod
    def build(
            node_spec: NodeSpec,
            session: SessionRegistry
    ) -> BaseNode:
        # 1) Lookup the BaseFactory subclass and its Pydantic schema
        try:
            factory_cls = element_registry.get_factory_or_class(node_spec.name)  # must be a BaseFactory subclass
            schema = element_registry.get_schema(node_spec.name)  # must be a BaseNodeConfig subclass
        except KeyError:
            raise PluginConfigurationError(
                f"No factory or schema registered for node type '{node_spec.type}'",
                node_spec.dict()
            )

        if schema is None or not issubclass(schema, BaseNodeConfig):
            raise PluginConfigurationError(
                f"Invalid or missing config schema for node type '{node_spec.type}'",
                node_spec.dict()
            )

        # 2) Validate & merge the inline NodeSpec into a BaseNodeConfig
        try:
            cfg: BaseNodeConfig = schema(**node_spec.dict(exclude_unset=True))
        except ValidationError as ve:
            raise PluginConfigurationError(
                f"NodeSpec validation failed for '{node_spec.type}': {ve}",
                node_spec.dict()
            )

        # 3) Resolve all atomic dependencies from the session
        deps: Dict[str, Any] = {
            "llm": session.get_llm(cfg.llm) if cfg.llm else None,
            "retriever": session.get_retriever(cfg.retriever) if cfg.retriever else None,
            "tools": [session.get_tool(t) for t in cfg.tools],
        }

        # 4) Delegate to the factory for final instantiation
        factory: BaseFactory = factory_cls()
        if not factory.accepts(cfg):
            raise PluginConfigurationError(
                f"Factory '{factory_cls.__name__}' does not accept config for '{node_spec.type}'",
                cfg.dict()
            )

        try:
            node: BaseNode = factory.create(cfg, **deps)
        except Exception as e:
            raise PluginConfigurationError(
                f"{factory_cls.__name__}.create() failed for node '{node_spec.type}': {e}",
                cfg.dict()
            ) from e

        return node
