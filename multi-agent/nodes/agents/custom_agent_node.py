from typing import Any, Dict, List, Optional
from nodes.base_node import BaseNode, StreamWriter
from graph.state.graph_state import GraphState
from llms.chat.message import ChatMessage, Role


class CustomAgentNode(BaseNode):
    """
    An LLM-based agent node that can optionally retrieve context,
    build structured prompts, post-process responses with tools,
    and support both streaming and synchronous execution.
    """

    def _prepare_messages(self, state: GraphState) -> List[ChatMessage]:
        """Constructs system + user messages. Optionally retrieves context."""
        messages: List[ChatMessage] = state.get("messages", []).copy()
        if not messages:
            raise ValueError("State must contain at least one message.")

        # Add optional context
        if self.retriever:
            user_prompt = messages[-1].content
            context = self.retriever.retrieve(user_prompt)
            message_with_context = ChatMessage(role=Role.USER, content=f"context: {context}\nuser:\n{user_prompt}")
            messages[-1] = message_with_context

        # Prepend system message
        if self.system_message:
            messages.insert(0, ChatMessage(role=Role.SYSTEM, content=self.system_message))

        return messages

    def run(self, state: GraphState) -> GraphState:
        """Main execution logic, shared by run and stream."""
        messages = self._prepare_messages(state)
        response = self.call_llm(messages)

        for tool in self.tools:
            response = tool.invoke(response)

        state["nodes_output"] = {self.name: response}
        return state
