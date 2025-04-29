from registry.element_registry import ElementRegistry
from session.session_registry import SessionRegistry
from schemas.nodes.base_node import BaseNodeConfig
from schemas.blueprint.blueprint import NodeSpec
from nodes.base_node import BaseNode
from typing import Type, Dict


class NodeFactory:
    """
    Builds BaseNode instances by merging:
      • a registered template (BaseNodeConfig)
      • user overrides (NodeSpec)
      • session’s atomic instances (LLM, tools, retriever)
    """

    @staticmethod
    def build(
            node_spec: NodeSpec,
            session: SessionRegistry
    ) -> BaseNode:
        er = ElementRegistry()
        # 1) Load the template config for this type
        template_meta = er.get_metadata(node_spec.type)
        template_cfg = template_meta["config_schema"]
        assert issubclass(template_cfg, BaseNodeConfig), "Bad template schema"
        # 2) Retrieve stored defaults
        defaults: BaseNodeConfig = template_cfg.parse_obj(template_meta["cls"].__dict__)
        #    or if you store defaults differently, fetch from registry
        # 3) Merge overrides
        overrides: Dict = node_spec.dict(exclude_unset=True)
        merged = defaults.copy(update=overrides)

        # 4) Resolve atomic instances
        llm = session.get_llm(merged.llm) if merged.llm else None
        retriever = session.get_retriever(merged.retriever) if merged.retriever else None
        tools = [session.get_tool(t) for t in merged.tools]

        # 5) Instantiate the actual Node class
        NodeClass: Type[BaseNode] = er.get_class(merged.type)
        node = NodeClass(
            name=merged.name or merged.type,
            llm=llm,
            retriever=retriever,
            tools=tools,
            system_message=merged.system_message or "",
            retries=merged.retries
        )
        return node
