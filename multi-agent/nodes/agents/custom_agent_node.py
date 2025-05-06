from nodes.base_node import BaseNode
from typing import Dict, Any
from runtime.state.graph_state import GraphState


class CustomAgentNode(BaseNode):
    """
    Wraps an LLM + optional retriever + tools + system prompt
    to implement “agent” semantics:
    - Optionally retrieve context
    - Ask LLM with system + user messages
    - Post-process / tool invocation
    """

    def run(self, state: dict) -> dict:
        # 1) Optionally fetch context
        if self.retriever:
            context = self.retriever.retrieve(state)
            state["context"] = context

        # 2) Build messages
        messages = []
        if self.system_message:
            messages.append({"role": "system", "content": self.system_message})
        messages.append({"role": "user", "content": state.get("user_prompt", "")})

        print(f"""user prompt: {state.get("user_prompt", "")}""")
        # 3) Call LLM
        response = self.llm.chat(messages)
        # print(f"""response: {response}""")
        # 4) Optionally use tools on response
        for tool in self.tools:
            response = tool.invoke(response)

        # 5) Store output
        state["nodes_output"] = {self.name: response}

        return state
