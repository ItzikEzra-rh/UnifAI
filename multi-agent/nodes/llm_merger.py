from nodes.base_node import BaseNode
from nodes.mixins.llm_capable import LlmCapableMixin
from graph.step_context import StepContext
from graph.state.graph_state import GraphState
from llms.chat.message import ChatMessage, Role


class LLMMergerNode(LlmCapableMixin, BaseNode):
    """
    Uses an LLM to merge outputs from multiple agents.
    """

    def __init__(self,
                 *,
                 step_ctx: StepContext,
                 name: str = "llm_merger",
                 llm,
                 system_message: str = "",
                 retries: int = 1):
        LlmCapableMixin.__init__(self,
                                 llm=llm,
                                 system_message=system_message,
                                 retries=retries)
        BaseNode.__init__(self, step_ctx=step_ctx, name=name)

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
        state["messages"] = [ChatMessage(role=Role.ASSISTANT, content=answer)]
        state["output"] = answer
        return state
