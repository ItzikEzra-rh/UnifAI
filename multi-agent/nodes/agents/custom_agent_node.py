from typing import Any, Dict, List, Optional
from nodes.base_node import BaseNode, StreamWriter
from graph.graph_state import GraphState


class CustomAgentNode(BaseNode):
    """
    An LLM-based agent node that can optionally retrieve context,
    build structured prompts, post-process responses with tools,
    and support both streaming and synchronous execution.
    """

    def _prepare_messages(self, state: GraphState) -> List[Dict[str, str]]:
        """Constructs system + user messages. Retrieves context if needed."""
        if self.retriever:
            # Retrieve context based on the user prompt and store it in the state
            state["context"] = self.retriever.retrieve(state.get("user_prompt", ""))

        messages = []
        if self.system_message:
            messages.append({"role": "system", "content": self.system_message})
        msg = f"""context: {state['context']}"\n {state.get("user_prompt", "")}"""
        messages.append({"role": "user", "content": msg})
        return messages

    def run(self, state: GraphState) -> GraphState:
        """Main execution logic, shared by run and stream."""
        messages = self._prepare_messages(state)
        response = self.call_llm(messages)  # handles both streaming and non-streaming
        for tool in self.tools:
            response = tool.invoke(response)
        state["nodes_output"] = {self.name: response}

        return state
