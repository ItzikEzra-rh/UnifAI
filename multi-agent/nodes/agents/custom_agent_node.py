from graph.state.graph_state import GraphState
from graph.step_context import StepContext
from llms.chat.message import ChatMessage, Role
from nodes.base_node import BaseNode
from nodes.mixins.llm_capable import LlmCapableMixin
from nodes.mixins.retriever_capable import RetrieverCapableMixin
from nodes.mixins.tool_capable import ToolCapableMixin


class CustomAgentNode(LlmCapableMixin,
                      RetrieverCapableMixin,
                      ToolCapableMixin,
                      BaseNode):
    """
    Full agent: LLM + optional retriever + optional tools.
    MRO guarantees LlmCapableMixin sees _stream() and uid from BaseNode.
    """

    def __init__(self,
                 *,
                 step_ctx: StepContext,
                 name: str,
                 llm,
                 retriever=None,
                 tools=(),
                 system_message="",
                 retries=1):

        LlmCapableMixin.__init__(self, llm=llm,
                                 system_message=system_message,
                                 retries=retries)
        RetrieverCapableMixin.__init__(self, retriever=retriever)
        ToolCapableMixin.__init__(self, tools=tools)
        BaseNode.__init__(self, step_ctx=step_ctx, name=name)

    def _prepare_messages(self, state: GraphState) -> list[ChatMessage]:
        msgs = state.get("messages", []).copy()
        if not msgs:
            raise ValueError("state['messages'] missing")

        if self.retriever:
            prompt = msgs[-1].content
            ctx = self._retrieve(prompt)
            msgs[-1] = ChatMessage(
                role=Role.USER,
                content=f"context: {ctx}\nuser:\n{prompt}"
            )

        if self.system_message:
            msgs.insert(0, ChatMessage(role=Role.SYSTEM, content=self.system_message))
        return msgs

    def run(self, state: GraphState) -> GraphState:
        msgs = self._prepare_messages(state)
        answer = self._chat(msgs)
        answer = self._apply_tools(answer)
        state["nodes_output"] = {self.name: answer}
        return state
