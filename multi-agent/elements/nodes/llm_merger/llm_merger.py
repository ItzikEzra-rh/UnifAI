from elements.nodes.common.base_node import BaseNode
from elements.nodes.common.capabilities.llm_capable import LlmCapableMixin
from graph.state.graph_state import GraphState
from elements.llms.common.chat.message import ChatMessage, Role


class LLMMergerNode(LlmCapableMixin, BaseNode):
    """
    Uses an LLM to merge outputs from multiple agents.
    """

    def __init__(self,
                 *,
                 name: str = "llm_merger",
                 llm,
                 system_message: str = "",
                 retries: int = 1,
                 **kwargs):
        super().__init__(name=name,
                         llm=llm,
                         system_message=system_message,
                         retries=retries,
                         **kwargs)

    def run(self, state: GraphState) -> GraphState:
        messages: list[ChatMessage] = state.get("messages", []).copy()

        if self.system_message:
            messages.insert(0, ChatMessage(role=Role.SYSTEM,
                                           content=self.system_message))

        # collate upstream outputs
        agents_output = state.get("nodes_output", {})
        user_q = state.get("user_prompt", "")
        user_block = "\n".join(f"{k}: {v}" for k, v in agents_output.items())
        merged_prompt = f"context:\n{user_block}\n\nuser question: {user_q}"
        messages.append(ChatMessage(role=Role.USER, content=merged_prompt))

        answer = self._chat(messages)
        state["messages"] = [answer]
        return state
