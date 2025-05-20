from .base_node import BaseNode, StreamWriter
from graph.state.graph_state import GraphState
from llms.chat.message import ChatMessage, Role


class LLMMergerNode(BaseNode):
    """
    A node that merges the output of multiple nodes using an LLM and a custom system prompt.
    """

    def run(self, state: GraphState) -> GraphState:
        # Build messages
        messages: list[ChatMessage] = state.get("messages", []).copy()

        if self.system_message:
            messages.insert(0, ChatMessage(role=Role.SYSTEM, content=self.system_message))

        # Extract output from agents
        agents_output = state.get("nodes_output", {})
        agents_output_str = "context:\n"

        for agent_name, output in agents_output.items():
            agents_output_str += f"{agent_name}: {output}\n"

        user_prompt = state.get("user_prompt", "")
        agents_output_str += f"\nuser question: {user_prompt}"

        messages.append(ChatMessage(role=Role.USER, content=agents_output_str))

        # Call LLM
        response = self.call_llm(messages)

        state["messages"] = [ChatMessage(role=Role.ASSISTANT, content=response)]

        # Save to state
        state["output"] = response
        return state
