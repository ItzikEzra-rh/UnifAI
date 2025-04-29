from nodes.base_node import BaseNode
from typing import Dict, Any


class CustomAgentNode(BaseNode):
    """
    Wraps an LLM + optional retriever + tools + system prompt
    to implement “agent” semantics:
    - Optionally retrieve context
    - Ask LLM with system + user messages
    - Post-process / tool invocation
    """

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        # 1) Optionally fetch context
        if self.retriever:
            context = self.retriever.retrieve(state)
            state["context"] = context

        # 2) Build messages
        messages = []
        if self.system_message:
            messages.append({"role": "system", "content": self.system_message})
        messages.append({"role": "user", "content": state.get("input", "")})

        # 3) Call LLM
        response = self.llm.chat(messages)

        # 4) Optionally use tools on response
        for tool in self.tools:
            response = tool.invoke(response)

        state["output"] = response
        return state
