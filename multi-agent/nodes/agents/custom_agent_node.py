from graph.state.graph_state import GraphState
from graph.step_context import StepContext
from llms.chat.message import ChatMessage, Role
from nodes.base_node import BaseNode
from nodes.mixins.llm_capable import LlmCapableMixin
from nodes.mixins.retriever_capable import RetrieverCapableMixin
from nodes.mixins.tool_capable import ToolCapableMixin
from typing import Any, Optional


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
                 llm: Any,
                 retriever: Any = None,
                 tools=(),
                 system_message: str = "",
                 retries: int = 1,
                 **kwargs: Any):

        super().__init__(step_ctx=step_ctx,
                         name=name,
                         llm=llm,
                         system_message=system_message,
                         retries=retries,
                         retriever=retriever,
                         tools=tools,
                         **kwargs)

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
        # 1) Prepare initial history (system + retrieval + user)
        history = self._prepare_messages(state)

        # 2) If no tools, one simple chat and return
        if not self.tools:
            assistant = self._chat(messages=history)
            state["nodes_output"] = {self.uid: assistant.content}
            return state

        # 3) Bind tools once
        self._llm_bind_tools(self.tools)

        max_rounds = 5
        assistant: Optional[ChatMessage] = None
        final_reply: Optional[ChatMessage] = None

        # 4) Call–invoke loop
        for _ in range(max_rounds):
            assistant = self._llm_sync_chat(messages=history)
            history.append(assistant)

            if assistant.tool_calls:
                tool_msgs = self.invoke_tools(assistant)
                history.extend(tool_msgs)
                # Loop so the LLM can see tool outputs
                continue

            # No further tool calls ⇒ this is our final answer
            final_reply = assistant
            break

        # 5) Fallback: ensure we have something
        assert assistant is not None, "LLM did not produce any response"
        if final_reply is None:
            final_reply = assistant

        # 6) Write out final content
        state["nodes_output"] = {self.uid: final_reply.content}
        return state
