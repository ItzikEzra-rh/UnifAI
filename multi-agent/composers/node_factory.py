from typing import Any, Dict
from pydantic import ValidationError
from graph.step_context import StepContext
from registry import element_registry
from session.session_registry import SessionRegistry
from schemas.nodes.base_node import NodeBaseConfig
from schemas.blueprint.blueprint import NodeSpec
from plugins.base_factory import BaseFactory
from plugins.exceptions import PluginConfigurationError
from nodes.base_node import BaseNode
from core.enums import ResourceCategory


class NodeFactory:
    """
    Orchestrates creation of BaseNode instances. Steps:

      1) Lookup ElementDefinition by category="node", type_key=node_spec.type
      2) Validate & merge inline overrides via Pydantic schema
      3) Resolve session-scoped dependencies (llm, retriever, tools)
      4) Delegate instantiation to factory.create(cfg, **deps)
    """

    @staticmethod
    def build(
            node_spec: NodeSpec,
            session: SessionRegistry,
            step_ctx: StepContext
    ) -> BaseNode:
        # 1) Lookup the factory class & config schema by (category, type_key)
        try:
            factory_cls = element_registry.get_factory(ResourceCategory.NODE, node_spec.type)
            schema_cls = element_registry.get_schema(ResourceCategory.NODE, node_spec.type)
        except ValueError:
            raise PluginConfigurationError(
                f"No factory/schema registered for node type '{node_spec.type}'",
                node_spec.dict()
            )

        # Ensure the schema is a subclass of our base config
        if schema_cls is None or not issubclass(schema_cls, NodeBaseConfig):
            raise PluginConfigurationError(
                f"Invalid or missing config schema for node type '{node_spec.type}'",
                node_spec.dict()
            )

        # 2) Validate & merge overrides
        try:
            cfg: NodeBaseConfig = schema_cls(**node_spec.dict(exclude_unset=True))
        except ValidationError as ve:
            raise PluginConfigurationError(
                f"NodeSpec validation failed for '{node_spec.type}': {ve}",
                node_spec.dict()
            )

        # 3) Resolve dependencies from the session
        deps: Dict[str, Any] = {
            "llm": session.get(ResourceCategory.LLM, cfg.llm) if cfg.llm else None,
            "retriever": session.get(ResourceCategory.RETRIEVER, cfg.retriever) if cfg.retriever else None,
            "tools": [session.get(ResourceCategory.TOOL, t) for t in cfg.tools],
            "step_ctx": step_ctx
        }

        # 4) Instantiate via the factory
        factory: BaseFactory = factory_cls()
        if not factory.accepts(cfg):
            raise PluginConfigurationError(
                f"Factory '{factory_cls.__name__}' rejects config for '{node_spec.type}'",
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
