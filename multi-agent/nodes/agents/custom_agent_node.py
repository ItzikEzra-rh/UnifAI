from typing import Any, Dict, List, Optional
from nodes.base_node import BaseNode, StreamWriter


class CustomAgentNode(BaseNode):
    """
    An LLM-based agent node that can optionally retrieve context,
    build structured prompts, post-process responses with tools,
    and support both streaming and synchronous execution.
    """

    def _prepare_messages(self, state: Dict[str, Any]) -> List[Dict[str, str]]:
        """Constructs system + user messages. Retrieves context if needed."""
        if self.retriever:
            state["context"] = self.retriever.retrieve(state)

        messages = []
        if self.system_message:
            messages.append({"role": "system", "content": self.system_message})
        messages.append({"role": "user", "content": state.get("user_prompt", "")})
        return messages

    def run(self, state: dict) -> dict:
        """Main execution logic, shared by run and stream."""
        messages = self._prepare_messages(state)
        response = self.call_llm(messages)  # handles both streaming and non-streaming
        for tool in self.tools:
            response = tool.invoke(response)
        state["nodes_output"] = {self.name: response}

        return state
